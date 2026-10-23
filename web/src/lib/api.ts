import type { Health, Prediction } from "./types";

export async function predict(text: string, strict: boolean): Promise<Prediction> {
  const response = await fetch("/api/predict", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ messages: [text], strict }),
  });
  if (!response.ok) {
    throw new Error(
      response.status === 422 ? "A message must be 1 to 2,000 characters."
        : response.status === 401 ? "This service needs an API key."
        : "The service could not answer. Try again in a moment.",
    );
  }
  return (await response.json()).results[0];
}

export async function health(): Promise<Health> {
  const response = await fetch("/api/health");
  if (!response.ok) throw new Error("status " + response.status);
  return response.json();
}
