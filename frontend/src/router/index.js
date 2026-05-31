import { createRouter, createWebHistory } from "vue-router";

const routes = [
  {
    path: "/",
    name: "welcome",
    component: () => import("../views/WelcomePage.vue"),
  },
  {
    path: "/learn",
    name: "learn",
    component: () => import("../views/LearningShell.vue"),
  },
  // 预留扩展：后续可添加更多路由
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
