"use client";

import { DataTable } from "@/components/data-table";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator } from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { BACKEND_PUBLIC_URL } from "@/lib/api-utils";
import { FileMetadata } from "@/types";
import { DialogTrigger } from "@radix-ui/react-dialog";
import { DropdownMenuTrigger } from "@radix-ui/react-dropdown-menu";
import { ColumnDef } from "@tanstack/react-table";
import { MoreHorizontal, Upload } from "lucide-react";
import { useState } from "react";

import { useEffect } from "react";

import {toast} from "sonner"

export default function Files() {
  const [files, setFiles] = useState<FileMetadata[]>([]);
  const [dialogOpen, setDialogOpen] = useState(false);
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

  const columnDefs: ColumnDef<FileMetadata>[] = [
    {
      header: "Name",
      accessorKey: "name",
    },
    {
      header: "Size",
      accessorKey: "size",  
    },
    {
      header: "Content Type",
      accessorKey: "content_type",
    },
    {
      id: "actions",
      header: "Actions",
      cell: ({row}) => {
        const file = row.original;
        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="h-8 w-8 p-0">
                <span className="sr-only">Open menu</span>
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={() =>
                  window.open(
                    `${BACKEND_PUBLIC_URL}/files/${file.id}/download`,
                    "_blank",
                  )
                }
              >
                Download
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => handleFileDelete(file.id)}
                className="text-destructive"
              >
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        );

      }
    }
  ];
    

  return (
    <div className="flex flex-col flex-1 m-4">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Files</h1>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Upload className="mr-2 h-4 w-4" />
              Upload File
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Upload File</DialogTitle>
              <DialogDescription>
                Choose a file from your device to upload.
              </DialogDescription>
            </DialogHeader>
            <div className="py-4">
              <Input
                type="file"
                id="file-upload"
                name="file"
                onChange={(e) => {
                  handleFileUpload(e);
                  setDialogOpen(false);
                }}
              />
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <DataTable columns={columnDefs} data={files} />
    </div>
  );
}
