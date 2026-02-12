import { useState } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { UploadPage } from "./pages/UploadPage";
import type { AnalysisResult } from "./types/analysis";

export default function App() {
  const [result, setResult] = useState<AnalysisResult | null>(null);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<UploadPage onResult={setResult} />} />
        <Route path="/dashboard" element={
          result ? <div>Dashboard placeholder</div> : <div>No data</div>
        } />
      </Routes>
    </BrowserRouter>
  );
}
