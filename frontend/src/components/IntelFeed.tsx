export function IntelFeed() {
  return (
    <div className="argus-card flex flex-col h-full">
      <div className="px-3 py-2.5 border-b border-argus-border flex items-center justify-between">
        <span className="argus-label">INTELLIGENCE FEED</span>
        <span className="font-mono text-xxs text-argus-neutral tabular-nums">0 EVENTS</span>
      </div>

      <div className="flex-1 flex items-center justify-center p-6">
        <div className="text-center space-y-3">
          <div className="w-10 h-10 mx-auto border border-argus-border rounded-full flex items-center justify-center">
            <span className="font-mono text-xs text-argus-neutral">AI</span>
          </div>
          <div>
            <p className="font-mono text-xxs text-argus-neutral tracking-wider">
              AWAITING LAYER 2
            </p>
            <p className="font-mono text-xxs text-argus-neutral/50 mt-1">
              YOLO26s detection events will appear here
            </p>
          </div>

          {/* Decorative future items */}
          <div className="pt-3 space-y-2">
            {['L1 — INSTANT ALERTS', 'L2 — CONTEXT ENRICHMENT', 'L3 — PREDICTIVE REASONING'].map((label) => (
              <div
                key={label}
                className="flex items-center gap-2 px-3 py-1.5 border border-argus-border/50 opacity-30"
              >
                <span className="w-1 h-1 rounded-full bg-argus-neutral" />
                <span className="font-mono text-xxs text-argus-neutral tracking-wider">
                  {label}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
