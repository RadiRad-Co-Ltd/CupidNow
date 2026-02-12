export function ShareCTA() {
  return (
    <section
      className="flex w-full flex-col items-center"
      style={{
        background:
          "linear-gradient(160deg, #FFF8FA 0%, #FDF0F5 50%, #EDE4F5 100%)",
        padding: "64px 120px",
      }}
    >
      <h2 className="mb-3 text-center font-heading text-[32px] font-bold text-text-primary">
        分享你們的心動報告
      </h2>
      <p className="mb-8 text-center font-body text-[16px] text-text-secondary">
        生成一張精美的報告摘要卡，與朋友分享你們的互動數據
      </p>

      <div className="flex items-center gap-4">
        {/* Primary button */}
        <button
          type="button"
          onClick={() => alert("Coming soon!")}
          className="rounded-full font-body text-[16px] font-semibold text-white transition-opacity hover:opacity-90"
          style={{
            background:
              "linear-gradient(135deg, #E8457E 0%, #9F7AEA 100%)",
            padding: "16px 36px",
            boxShadow: "0 6px 24px 0 #E8457E30",
          }}
        >
          {"\uD83D\uDD17"} 生成分享卡
        </button>

        {/* Secondary button */}
        <button
          type="button"
          onClick={() => alert("Coming soon!")}
          className="rounded-full border border-border-light bg-white font-body text-[16px] font-semibold text-text-primary transition-colors hover:bg-gray-50"
          style={{ padding: "16px 36px" }}
        >
          {"\uD83D\uDCE5"} 下載完整報告
        </button>
      </div>
    </section>
  );
}
