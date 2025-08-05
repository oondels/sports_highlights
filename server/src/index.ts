import express, { Request, Response, NextFunction } from 'express';
import multer from 'multer';
import { createClient } from '@supabase/supabase-js';
import { v4 as uuid } from 'uuid';
import path from 'path';
import dotenv from 'dotenv';
dotenv.config();

const app = express();
const upload = multer({ storage: multer.memoryStorage() });

// Initialize Supabase client with service role key (secure, only on server)
const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_KEY!
);

app.get("/", (req: Request, res: Response) => {
  res.send("Video upload api is running.");
})

app.post('/api/videos', upload.single('file'), async (req: Request, res: Response) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No file uploaded.' });
  }

  const fileExt = path.extname(req.file.originalname);
  const filename = `${uuid()}${fileExt}`;
  const bucket = process.env.BUCKET_NAME || 'sports.highlights';

  console.log(`Bucket: ${bucket}`);
  

  // Upload to Supabase Storage
  const { data: uploadData, error: uploadError } = await supabase
    .storage
    .from(bucket)
    .upload(filename, req.file.buffer, {
      contentType: req.file.mimetype,
      upsert: false
    });

  if (uploadError || !uploadData) {
    console.error('Supabase upload error:', uploadError);
    res.status(500).json({ error: 'Upload failed.' });
    return
  }

  const filePath = uploadData.path;


  // (Optionally) save metadata to your database here
  // e.g. INSERT INTO videos (id, path, uploaded_at) VALUES (...)

  // Respond with the public URL (or a signed URL)
  const { data: urlData } = supabase
    .storage
    .from(bucket)
    .getPublicUrl(filePath);

  if (!urlData) {
    console.error('Supabase getPublicUrl error');
    res.status(500).json({ error: 'Could not get public URL.' });
    return
  }

  res.status(201).json({
    id: filename,
    url: urlData.publicUrl,
  });
});

const port = process.env.PORT || 3000;
app.listen(port, () => {
  console.log(`Listening on http://localhost:${port}`);
});

