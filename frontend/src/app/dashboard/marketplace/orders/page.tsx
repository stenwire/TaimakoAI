'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ClipboardList,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  CheckCircle,
  X,
  Eye,
  Filter,
  Package,
} from 'lucide-react';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import SkeletonLoader from '@/components/ui/SkeletonLoader';
import Modal from '@/components/ui/Modal';
import { listOrders, updateOrderStatus } from '@/lib/api';
import { Order, OrderStatus } from '@/lib/types';

const STATUS_STYLES: Record<OrderStatus, string> = {
  pending:    'bg-yellow-100 text-yellow-700',
  confirmed:  'bg-blue-100 text-blue-700',
  processing: 'bg-orange-100 text-orange-700',
  shipped:    'bg-purple-100 text-purple-700',
  delivered:  'bg-green-100 text-green-700',
  cancelled:  'bg-gray-100 text-gray-600',
};

const ALL_STATUSES: OrderStatus[] = ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled'];

const PAGE_SIZE = 20;

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [updatingStatus, setUpdatingStatus] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const showNotification = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 5000);
  };

  const fetchOrders = useCallback(async () => {
    setLoading(true);
    try {
      const res = await listOrders({ page, page_size: PAGE_SIZE, status: statusFilter });
      setOrders(res.items);
      setTotal(res.total);
      setPages(res.pages);
    } catch {
      showNotification('error', 'Failed to load orders');
    } finally {
      setLoading(false);
    }
  }, [page, statusFilter]);

  useEffect(() => {
    fetchOrders();
  }, [fetchOrders]);

  useEffect(() => {
    setPage(1);
  }, [statusFilter]);

  const handleStatusChange = async (orderId: string, newStatus: string) => {
    setUpdatingStatus(true);
    try {
      const updated = await updateOrderStatus(orderId, newStatus);
      setOrders((prev) => prev.map((o) => (o.id === orderId ? updated : o)));
      if (selectedOrder?.id === orderId) setSelectedOrder(updated);
      showNotification('success', 'Order status updated');
    } catch {
      showNotification('error', 'Failed to update status');
    } finally {
      setUpdatingStatus(false);
    }
  };

  const shortId = (id: string) => id.slice(0, 8).toUpperCase();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-[var(--brand-primary)]/10 rounded-[var(--radius-squircle)]">
            <ClipboardList className="w-8 h-8 text-[var(--brand-primary)]" />
          </div>
          <div>
            <h1 className="text-h1 text-[var(--text-primary)]">Orders</h1>
            <p className="text-body text-[var(--text-secondary)] mt-1">
              Track orders placed via the Sales Agent
            </p>
          </div>
        </div>
        <Button variant="secondary" onClick={fetchOrders}>
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Notifications */}
      <AnimatePresence>
        {message && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className={`p-4 rounded-[var(--radius-md)] flex items-start gap-3 shadow-sm border ${
              message.type === 'success'
                ? 'bg-green-50 border-green-200 text-green-700'
                : 'bg-red-50 border-red-200 text-red-700'
            }`}
          >
            {message.type === 'success' ? (
              <CheckCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            ) : (
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            )}
            <p className="text-small font-medium">{message.text}</p>
            <button onClick={() => setMessage(null)} className="ml-auto">
              <X className="w-4 h-4 opacity-50 hover:opacity-100" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Filter bar */}
      <Card className="p-4">
        <div className="flex items-center gap-3">
          <Filter className="w-4 h-4 text-[var(--text-tertiary)]" />
          <span className="text-sm text-[var(--text-secondary)]">Status:</span>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setStatusFilter('')}
              className={`px-3 py-1 rounded-full text-xs font-semibold transition-colors ${
                statusFilter === ''
                  ? 'bg-[var(--brand-primary)] text-white'
                  : 'bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]'
              }`}
            >
              All
            </button>
            {ALL_STATUSES.map((s) => (
              <button
                key={s}
                onClick={() => setStatusFilter(s)}
                className={`px-3 py-1 rounded-full text-xs font-semibold capitalize transition-colors ${
                  statusFilter === s
                    ? 'bg-[var(--brand-primary)] text-white'
                    : 'bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]'
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      </Card>

      {/* Orders Table */}
      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[var(--bg-secondary)] border-b border-[var(--border-subtle)]">
                <th className="px-6 py-4 text-xs font-semibold text-[var(--text-tertiary)] uppercase tracking-wider">Order ID</th>
                <th className="px-6 py-4 text-xs font-semibold text-[var(--text-tertiary)] uppercase tracking-wider">Customer</th>
                <th className="px-6 py-4 text-xs font-semibold text-[var(--text-tertiary)] uppercase tracking-wider">Items</th>
                <th className="px-6 py-4 text-xs font-semibold text-[var(--text-tertiary)] uppercase tracking-wider">Total</th>
                <th className="px-6 py-4 text-xs font-semibold text-[var(--text-tertiary)] uppercase tracking-wider">Status</th>
                <th className="px-6 py-4 text-xs font-semibold text-[var(--text-tertiary)] uppercase tracking-wider">Date</th>
                <th className="px-6 py-4 text-right"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border-subtle)]">
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i}>
                    <td colSpan={7} className="px-6 py-4">
                      <SkeletonLoader variant="text" />
                    </td>
                  </tr>
                ))
              ) : orders.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center">
                    <Package className="w-12 h-12 text-[var(--text-tertiary)] mx-auto mb-3 opacity-20" />
                    <p className="text-[var(--text-secondary)]">
                      {statusFilter ? `No ${statusFilter} orders` : 'No orders yet'}
                    </p>
                    <p className="text-xs text-[var(--text-tertiary)] mt-1">
                      Orders placed via the Sales Agent will appear here
                    </p>
                  </td>
                </tr>
              ) : (
                orders.map((order) => (
                  <tr key={order.id} className="hover:bg-[var(--bg-secondary)]/50 transition-colors group">
                    <td className="px-6 py-4 font-mono text-xs text-[var(--text-secondary)]">
                      #{shortId(order.id)}
                    </td>
                    <td className="px-6 py-4">
                      <p className="text-sm font-medium text-[var(--text-primary)]">{order.customer_name}</p>
                      {order.customer_email && (
                        <p className="text-xs text-[var(--text-tertiary)]">{order.customer_email}</p>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm text-[var(--text-secondary)]">
                      {order.items.length} item{order.items.length !== 1 ? 's' : ''}
                      <p className="text-xs text-[var(--text-tertiary)] truncate max-w-[160px]">
                        {order.items.map((i) => i.product_name).join(', ')}
                      </p>
                    </td>
                    <td className="px-6 py-4 text-sm font-semibold text-[var(--text-primary)]">
                      {order.currency} {Number(order.total_amount).toFixed(2)}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${STATUS_STYLES[order.status]}`}>
                        {order.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-xs text-[var(--text-tertiary)]">
                      {new Date(order.created_at).toLocaleDateString('en-GB', {
                        day: 'numeric', month: 'short', year: 'numeric',
                      })}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setSelectedOrder(order)}
                        className="opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {!loading && total > 0 && (
          <div className="px-6 py-4 border-t border-[var(--border-subtle)] flex items-center justify-between">
            <p className="text-sm text-[var(--text-secondary)]">
              Showing {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, total)} of {total} orders
            </p>
            <div className="flex items-center gap-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <span className="text-sm text-[var(--text-primary)] px-1">
                {page} / {pages}
              </span>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setPage((p) => Math.min(pages, p + 1))}
                disabled={page === pages}
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        )}
      </Card>

      {/* Order Detail Modal */}
      {selectedOrder && (
        <Modal
          isOpen={!!selectedOrder}
          onClose={() => setSelectedOrder(null)}
          title={`Order #${shortId(selectedOrder.id)}`}
        >
          <div className="space-y-5">
            {/* Customer info */}
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-xs text-[var(--text-tertiary)] uppercase font-semibold mb-1">Customer</p>
                <p className="font-medium text-[var(--text-primary)]">{selectedOrder.customer_name}</p>
                {selectedOrder.customer_email && <p className="text-[var(--text-secondary)]">{selectedOrder.customer_email}</p>}
                {selectedOrder.customer_phone && <p className="text-[var(--text-secondary)]">{selectedOrder.customer_phone}</p>}
              </div>
              <div>
                <p className="text-xs text-[var(--text-tertiary)] uppercase font-semibold mb-1">Delivery Address</p>
                <p className="text-[var(--text-secondary)]">{selectedOrder.customer_address || '—'}</p>
              </div>
              <div>
                <p className="text-xs text-[var(--text-tertiary)] uppercase font-semibold mb-1">Placed</p>
                <p className="text-[var(--text-secondary)]">
                  {new Date(selectedOrder.created_at).toLocaleString('en-GB', {
                    day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
                  })}
                </p>
              </div>
              {selectedOrder.notes && (
                <div className="col-span-2">
                  <p className="text-xs text-[var(--text-tertiary)] uppercase font-semibold mb-1">Notes</p>
                  <p className="text-[var(--text-secondary)]">{selectedOrder.notes}</p>
                </div>
              )}
            </div>

            {/* Items */}
            <div>
              <p className="text-xs text-[var(--text-tertiary)] uppercase font-semibold mb-2">Items</p>
              <div className="border border-[var(--border-subtle)] rounded-[var(--radius-md)] overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-[var(--bg-secondary)] border-b border-[var(--border-subtle)]">
                      <th className="px-4 py-2 text-left text-xs font-semibold text-[var(--text-tertiary)]">Product</th>
                      <th className="px-4 py-2 text-right text-xs font-semibold text-[var(--text-tertiary)]">Qty</th>
                      <th className="px-4 py-2 text-right text-xs font-semibold text-[var(--text-tertiary)]">Unit</th>
                      <th className="px-4 py-2 text-right text-xs font-semibold text-[var(--text-tertiary)]">Total</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border-subtle)]">
                    {selectedOrder.items.map((item) => (
                      <tr key={item.id}>
                        <td className="px-4 py-2 text-[var(--text-primary)]">
                          {item.product_name}
                          <span className="text-xs text-[var(--text-tertiary)] ml-1">({item.product_sku})</span>
                        </td>
                        <td className="px-4 py-2 text-right text-[var(--text-secondary)]">{item.quantity}</td>
                        <td className="px-4 py-2 text-right text-[var(--text-secondary)]">
                          {item.currency} {Number(item.unit_price).toFixed(2)}
                        </td>
                        <td className="px-4 py-2 text-right font-semibold text-[var(--text-primary)]">
                          {item.currency} {Number(item.total_price).toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr className="border-t border-[var(--border-subtle)] bg-[var(--bg-secondary)]">
                      <td colSpan={3} className="px-4 py-2 text-right font-semibold text-sm text-[var(--text-primary)]">
                        Total
                      </td>
                      <td className="px-4 py-2 text-right font-bold text-[var(--text-primary)]">
                        {selectedOrder.currency} {Number(selectedOrder.total_amount).toFixed(2)}
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>

            {/* Status update */}
            <div>
              <p className="text-xs text-[var(--text-tertiary)] uppercase font-semibold mb-2">Update Status</p>
              <div className="flex flex-wrap gap-2">
                {ALL_STATUSES.map((s) => (
                  <button
                    key={s}
                    disabled={selectedOrder.status === s || updatingStatus}
                    onClick={() => handleStatusChange(selectedOrder.id, s)}
                    className={`px-3 py-1.5 rounded-full text-xs font-bold capitalize transition-all ${
                      selectedOrder.status === s
                        ? `${STATUS_STYLES[s]} ring-2 ring-offset-1 ring-current`
                        : 'bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] disabled:opacity-40'
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
