export async function submitSignup(email, post) {
  if (!email.includes("@")) {
    return { message: "Enter a valid email", clear: false };
  }
  const res = await post("/api/signup", { email });
  if (res.status === 201) {
    return { message: "Check your inbox to confirm", clear: true };
  }
  return { message: "Something went wrong, try again", clear: false };
}
