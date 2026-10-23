type UploadViewProps = {
  error: string | null;
  fileName: string | null;
  onFileSelected: (file: File) => void;
  onTrySample: () => void;
};

export function UploadView({ error, fileName, onFileSelected, onTrySample }: UploadViewProps) {
  const select = (file: File | undefined) => { if (file) void onFileSelected(file); };
  return (
    <section className="upload-view" aria-labelledby="upload-title">
      <div className="upload-view__intro">
        <p className="eyebrow">Evidence, not a score</p>
        <h1 id="upload-title">Does your demo prove its claims?</h1>
        <p>
          Map each product claim to the exact moment your demo proves it on screen.
        </p>
      </div>
      <div className="drop-zone" onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); select(event.dataTransfer.files[0]); }}>
        <span className="drop-zone__icon" aria-hidden="true">↑</span>
        <h2>Drop an MP4 demo</h2>
        <p>Up to 3 minutes · English narration only · H.264 MP4 recommended</p>
        <label className="secondary-button upload-button">{fileName ?? "Choose video"}<input accept="video/mp4" onChange={(event) => select(event.target.files?.[0])} type="file" /></label>
        {fileName && <p className="upload-ready">Ready: {fileName}</p>}
        {error && <p className="error-message">{error}</p>}
      </div>
      <div className="sample-cta">
        <div>
          <p className="eyebrow">No video handy?</p>
          <p>See a recorded Claude analysis of a scripted TodoMVC demo, without uploading anything.</p>
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
