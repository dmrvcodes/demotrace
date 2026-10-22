type UploadViewProps = {
  onTrySample: () => void;
};

export function UploadView({ onTrySample }: UploadViewProps) {
  return (
    <section className="upload-view" aria-labelledby="upload-title">
      <div className="upload-view__intro">
        <p className="eyebrow">Evidence, not a score</p>
        <h1 id="upload-title">Does your demo prove its claims?</h1>
        <p>
          Map each product claim to the exact moment your demo proves it on screen.
        </p>
      </div>
      <div className="drop-zone">
        <span className="drop-zone__icon" aria-hidden="true">↑</span>
        <h2>Drop an MP4 demo</h2>
        <p>Up to 3 minutes · English narration only · H.264 MP4 recommended</p>
        <button className="primary-button" disabled type="button">
          Upload coming next
        </button>
      </div>
      <div className="sample-cta">
        <div>
          <p className="eyebrow">No video handy?</p>
          <p>Inspect a sample evidence map without uploading anything.</p>
        </div>
        <button className="secondary-button" onClick={onTrySample} type="button">
          Try with sample
        </button>
      </div>
      <p className="privacy-copy">
        Video is deleted right after processing. If processing fails, it is removed automatically within a few days.
      </p>
    </section>
  );
}
