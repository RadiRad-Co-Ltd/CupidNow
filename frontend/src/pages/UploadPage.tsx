import type { AnalysisResult } from "../types/analysis";

interface Props {
  onResult: (result: AnalysisResult) => void;
}

export function UploadPage({ onResult: _onResult }: Props) {
  return <div>Upload page placeholder</div>;
}
