import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  vus: 10,
  duration: "30s",
};

const baseUrl = __ENV.BASE_URL || "http://localhost:8000";

function validPredictPayload() {
  return JSON.stringify({
    seller_id: 1,
    is_verified_seller: true,
    item_id: 1,
    name: "Test",
    description: "Some description for moderation",
    category: 1,
    images_qty: 3,
  });
}

function invalidPredictPayload() {
  return JSON.stringify({
    seller_id: -1,
    is_verified_seller: true,
    item_id: 0,
    name: "",
    description: "",
    category: 1,
    images_qty: -5,
  });
}

export default function () {
  const r = Math.random();

  if (r < 0.7) {
    const res = http.post(`${baseUrl}/predict`, validPredictPayload(), {
      headers: { "Content-Type": "application/json" },
    });
    check(res, {
      "predict status is 200": (x) => x.status === 200,
      "predict has probability": (x) => {
        try {
          const j = x.json();
          return typeof j.probability === "number";
        } catch {
          return false;
        }
      },
    });
  } else if (r < 0.9) {
    const res = http.post(`${baseUrl}/simple_predict`, JSON.stringify({ advertisement_id: 1 }), {
      headers: { "Content-Type": "application/json" },
    });
    check(res, {
      "simple_predict status is 200/404/503": (x) => [200, 404, 503].includes(x.status),
    });
  } else {
    const res = http.post(`${baseUrl}/predict`, invalidPredictPayload(), {
      headers: { "Content-Type": "application/json" },
    });
    check(res, {
      "invalid predict status is 422/400/500": (x) => [422, 400, 500].includes(x.status),
    });
  }

  sleep(0.1);
}
