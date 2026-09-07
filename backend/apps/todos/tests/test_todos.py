"""
These tests exercise the most important requirement of the assignment:
that Todos are strictly scoped to the authenticated account, and that
one account can never read, edit, or delete another account's Todos —
even by guessing/incrementing an id in the URL (IDOR).

Rather than minting real Auth0 tokens, we use DRF's
`APIClient.force_authenticate(user=<Account>)`, which exercises the
exact same permission/queryset code path (`request.user` is an
`Account` instance) without needing network access to Auth0. The JWT
verification itself is covered separately in test_authentication.py.
"""
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import Account
from apps.todos.models import Todo


class TodoIsolationTests(APITestCase):
    def setUp(self):
        self.account_a = Account.objects.create(auth0_user_id="auth0|user-a", email="a@example.com")
        self.account_b = Account.objects.create(auth0_user_id="auth0|user-b", email="b@example.com")

        self.todo_a = Todo.objects.create(account=self.account_a, title="A's private todo")
        self.todo_b = Todo.objects.create(account=self.account_b, title="B's private todo")

    def test_unauthenticated_request_is_rejected(self):
        response = self.client.get("/api/todos/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_only_sees_own_todos_in_list(self):
        self.client.force_authenticate(user=self.account_a)
        response = self.client.get("/api/todos/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [t["title"] for t in response.data["results"]]
        self.assertIn("A's private todo", titles)
        self.assertNotIn("B's private todo", titles)

    def test_user_cannot_retrieve_another_users_todo_by_id(self):
        """The core IDOR case from the assignment: GET /api/todos/<b's id>/ as user A."""
        self.client.force_authenticate(user=self.account_a)
        response = self.client.get(f"/api/todos/{self.todo_b.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_update_another_users_todo(self):
        self.client.force_authenticate(user=self.account_a)
        response = self.client.patch(
            f"/api/todos/{self.todo_b.id}/", {"completed": True}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.todo_b.refresh_from_db()
        self.assertFalse(self.todo_b.completed)

    def test_user_cannot_delete_another_users_todo(self):
        self.client.force_authenticate(user=self.account_a)
        response = self.client.delete(f"/api/todos/{self.todo_b.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Todo.objects.filter(id=self.todo_b.id).exists())

    def test_created_todo_is_owned_by_the_authenticated_account_not_client_input(self):
        """
        Even if a malicious client tries to smuggle an `account` field
        pointing at someone else, ownership must come from the token.
        """
        self.client.force_authenticate(user=self.account_a)
        response = self.client.post(
            "/api/todos/",
            {"title": "New todo", "account": self.account_b.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = Todo.objects.get(id=response.data["id"])
        self.assertEqual(created.account_id, self.account_a.id)


class TodoCRUDTests(APITestCase):
    def setUp(self):
        self.account = Account.objects.create(auth0_user_id="auth0|user-1", email="user1@example.com")
        self.client.force_authenticate(user=self.account)

    def test_create_todo(self):
        response = self.client.post(
            "/api/todos/", {"title": "Buy milk", "description": "2%"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Buy milk")
        self.assertFalse(response.data["completed"])

    def test_create_todo_requires_title(self):
        response = self.client.post("/api/todos/", {"title": "   "}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_empty_state(self):
        response = self.client.get("/api/todos/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], [])

    def test_mark_completed(self):
        todo = Todo.objects.create(account=self.account, title="Ship feature")
        response = self.client.patch(f"/api/todos/{todo.id}/", {"completed": True}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        todo.refresh_from_db()
        self.assertTrue(todo.completed)

    def test_delete_todo(self):
        todo = Todo.objects.create(account=self.account, title="Delete me")
        response = self.client.delete(f"/api/todos/{todo.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Todo.objects.filter(id=todo.id).exists())

    def test_filter_by_completed(self):
        Todo.objects.create(account=self.account, title="Done", completed=True)
        Todo.objects.create(account=self.account, title="Not done", completed=False)
        response = self.client.get("/api/todos/?completed=true")
        titles = [t["title"] for t in response.data["results"]]
        self.assertEqual(titles, ["Done"])

    def test_search_by_title(self):
        Todo.objects.create(account=self.account, title="Renew passport")
        Todo.objects.create(account=self.account, title="Buy milk")
        response = self.client.get("/api/todos/?search=passport")
        titles = [t["title"] for t in response.data["results"]]
        self.assertEqual(titles, ["Renew passport"])
