import { useState } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { UploadPage } from "./pages/UploadPage";
import { DashboardPage } from "./pages/DashboardPage";
import type { AnalysisResult } from "./types/analysis";
// DEV ONLY: mock data for dashboard preview — remove before production
import { mockResult } from "./data/mockResult";

export default function App() {
  const [result, setResult] = useState<AnalysisResult | null>(mockResult);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<UploadPage onResult={setResult} />} />
        <Route
          path="/dashboard"
          element={
            result ? (
              <DashboardPage result={result} />
            ) : (
              <Navigate to="/" replace />
            )
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
