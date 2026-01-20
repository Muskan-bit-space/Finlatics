import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:5000",
});


// ML: Fetch next-day return prediction
export const fetchReturnPrediction = async (ticker) => {
  try {
    const response = await api.get("/api/ml/predict", {
      params: { ticker }
    });

    return response.data;
  } catch (error) {
    console.error("Prediction API error:", error.message);
    return null;
  }
};

export default api;
