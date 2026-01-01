'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { FileText, RefreshCw, Database, Check } from 'lucide-react';
import { listDocuments, processDocuments } from '@/lib/api';
import type { Document } from '@/lib/types';

interface DocumentListProps {
  refreshTrigger: number;
}

export default function DocumentList({ refreshTrigger }: DocumentListProps) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processStatus, setProcessStatus] = useState<string | null>(null);

  const fetchDocuments = async () => {
    setIsLoading(true);
    try {
      const docs = await listDocuments();
      setDocuments(docs);
    } catch (error) {
      console.error('Failed to fetch documents:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [refreshTrigger]);

  const handleProcess = async () => {
    setIsProcessing(true);
    setProcessStatus(null);
    try {
      await processDocuments();
      setProcessStatus('Documents processed successfully!');
      setTimeout(() => setProcessStatus(null), 3000);
    } catch (error) {
      console.error('Processing failed:', error);
      setProcessStatus('Failed to process documents.');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-slate-200 flex items-center gap-2">
          <Database className="w-5 h-5 text-indigo-400" />
          Knowledge Base
        </h2>
        <button
          onClick={fetchDocuments}
          className="p-2 hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-indigo-400"
          title="Refresh list"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="bg-slate-900/50 rounded-xl border border-slate-700/50 overflow-hidden min-h-[200px]">
        {documents.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-[200px] text-slate-500">
            <FileText className="w-8 h-8 mb-2 opacity-50" />
            <p>No documents found</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-800">
            {documents.map((doc, i) => (
              <motion.div
                key={doc.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className="p-4 flex items-center gap-3 hover:bg-slate-800/50 transition-colors"
              >
                <div className="p-2 rounded-lg bg-slate-800 text-indigo-400">
                  <FileText className="w-4 h-4" />
                </div>
                <span className="text-sm text-slate-300">{doc.filename}</span>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      <div className="flex flex-col gap-3">
        <button
          onClick={handleProcess}
          disabled={isProcessing || documents.length === 0}
          className="w-full py-3 px-4 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-lg shadow-emerald-900/20"
        >
          {isProcessing ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              Processing Knowledge Base...
            </>
          ) : (
            <>
              <Database className="w-4 h-4" />
              Process Documents
            </>
          )}
        </button>

        {processStatus && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`text-sm text-center p-2 rounded-lg ${processStatus.includes('failed')
              ? 'bg-rose-500/10 text-rose-400'
              : 'bg-emerald-500/10 text-emerald-400'
              }`}
          >
            {processStatus}
          </motion.div>
        )}
      </div>
    </div>
  );
}
