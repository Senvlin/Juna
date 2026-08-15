import request from "./request";

export const apiService = {
  async fetchWords() {
    const [newResp, reviewResp] = await Promise.all([
      request.get("/word/new"),
      request.get("/word/review"),
    ]);
    const rawList = [...(reviewResp.data || []), ...(newResp.data || [])];
    return rawList;
  },

  async fetchNotes(wordData) {
    const resp = await request.post("/word/note/", wordData);
    return resp.data || [];
  },

  async sync(payload) {
    await request.post("/word/sync", payload);
  },

  async startLogin() {
    return request.post("/login/start");
  },

  async getLoginStatus(taskId) {
    return request.get(`/login/status/${taskId}`);
  },

  async getUserStatus() {
    return request.get("/user/status");
  },


};
