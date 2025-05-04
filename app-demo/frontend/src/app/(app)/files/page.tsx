"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FileMetadata } from "@/types";
import { useState } from "react";

import { useEffect } from "react";

import {toast} from "sonner"

export default function Files() {
  const [files, setFiles] = useState<FileMetadata[]>([]);

  useEffect(() => {
    const fetchFiles = async () => {
      const res = await fetch("/api/files");
      if (!res.ok) {
        toast.error("Failed to fetch files");
        return;
      }
      const data = await res.json();
      setFiles(data);
    };
    fetchFiles();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) {
      toast.error("No file selected");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch("/api/files", {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      toast.error("Failed to upload file");
      return;
    }

    const data = await res.json();
    setFiles([...files, data]);
  };

  const handleFileDelete = async (fileId: string) => {
    const res = await fetch(`/api/files/${fileId}`, {
      method: "DELETE",
    });

    if (!res.ok) {
      toast.error("Failed to delete file");
      return;
    }

    setFiles(files.filter((file) => file.id !== fileId));
  };


  return (
    <div>
      <Label htmlFor="file-upload">Upload File</Label>
      <Input type="file" id="file-upload" onChange={handleFileUpload} />

      {files.map((file) => (
        <div key={file.id}>
          <p>{file.name}</p>
          <p>{file.size}</p>
          <p>{file.content_type}</p>
          <a href={`/api/files/${file.id}/download`}>Download</a>
          <Button onClick={() => handleFileDelete(file.id)}>Delete</Button>
        </div>
      ))}
    </div>
  );
}
