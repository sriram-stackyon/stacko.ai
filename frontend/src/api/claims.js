import axios from "axios";

const client = axios.create({
  baseURL: "/api",
});

export async function submitClaim(formData) {
  const response = await client.post("/claims", formData);
  return response.data;
}

export async function getClaims() {
  const response = await client.get("/claims");
  return response.data;
}

export async function getClaimById(id) {
  const response = await client.get(`/claims/${id}`);
  return response.data;
}
