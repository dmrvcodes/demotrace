const HEVC_SAMPLE_ENTRY_TYPES = ["hvc1", "hev1", "dvhe", "dvh1"] as const;
const SCAN_BYTES = 2 * 1024 * 1024;

function includesAscii(bytes: Uint8Array, marker: string): boolean {
  const encoded = new TextEncoder().encode(marker);
  outer: for (let offset = 0; offset <= bytes.length - encoded.length; offset += 1) {
    for (let index = 0; index < encoded.length; index += 1) {
      if (bytes[offset + index] !== encoded[index]) continue outer;
    }
    return true;
  }
  return false;
}

/**
 * Detect HEVC sample-entry identifiers in the MP4's beginning and end.  ``moov`` may be
 * either fast-start (beginning) or regular (end) layout, so both parts are checked.
 * This is intentionally a client-side guardrail; ffprobe remains the server authority.
 */
export async function isHevcMp4(file: File): Promise<boolean> {
  const ranges = [file.slice(0, Math.min(SCAN_BYTES, file.size))];
  if (file.size > SCAN_BYTES) ranges.push(file.slice(Math.max(0, file.size - SCAN_BYTES)));
  const chunks = await Promise.all(ranges.map(async (range) => new Uint8Array(await range.arrayBuffer())));
  return chunks.some((chunk) => HEVC_SAMPLE_ENTRY_TYPES.some((marker) => includesAscii(chunk, marker)));
}
