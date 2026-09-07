export default function LoadingSpinner({ dark = false }: { dark?: boolean }) {
  return <span className={`spinner${dark ? " dark" : ""}`} aria-label="Loading" />;
}
