import { useCallback, useState } from "react";

interface Props {
  onFileSelected: (file: File) => void;
  disabled?: boolean;
}

export function FileDropzone({ onFileSelected, disabled }: Props) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file?.name.endsWith(".txt")) onFileSelected(file);
    },
    [onFileSelected]
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) onFileSelected(file);
  };

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      className={`
        flex flex-col items-center gap-4 rounded-3xl border-2 border-dashed p-12
        transition-colors duration-200
        ${isDragging ? "border-rose-primary bg-rose-soft" : "border-border-light bg-white"}
        ${disabled ? "opacity-50 pointer-events-none" : ""}
      `}
    >
      <div className="text-4xl">💌</div>
      <p className="font-heading text-lg font-bold text-text-primary">
        拖放或點擊上傳 LINE 對話記錄
      </p>
      <p className="text-sm text-text-secondary">
        支援 .txt 格式的 LINE 聊天記錄匯出檔
      </p>
      <label className="cursor-pointer rounded-xl bg-gradient-to-r from-rose-primary to-purple-accent px-8 py-3 font-body text-base font-semibold text-white shadow-lg transition hover:opacity-90">
        選擇檔案
        <input
          type="file"
          accept=".txt"
          onChange={handleChange}
          className="hidden"
          disabled={disabled}
        />
      </label>
    </div>
  );
}
