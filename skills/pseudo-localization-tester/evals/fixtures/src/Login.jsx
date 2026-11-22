export function Login() {
  return (
    <form>
      <h1>{t('login.title')}</h1>
      <label>Enter your user name</label>
      <input placeholder="Search products here" />
      <button>Submit</button>
      <p>Forgot your password?</p>
      <span>Photo Studio</span>
    </form>
  );
}
