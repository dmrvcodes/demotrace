# DemoTrace web

The Next.js frontend for DemoTrace. With `NEXT_PUBLIC_API_BASE_URL` set at build time it calls the
live AWS Control Lambda; **Try with sample** remains an instant interactive example and does not
call the backend.

```bash
npm install
npm run dev
```

Open `http://localhost:3000`, upload an MP4, and start a live analysis. You can also choose
**Try with sample** to inspect the interactive evidence map without uploading a video.

## Sample media attribution

`public/samples/demotrace-sample.mp4` starts with a DemoTrace promise slide authored for this project, followed by an excerpt of **Big Buck Bunny** by the Blender Foundation, used under [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/). The sample is an interface example only and will be replaced by an owned TodoMVC recording and its genuine recorded result before public submission.
