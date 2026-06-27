'use client';

import React, { useState, useEffect } from 'react';
import NextImage from 'next/image';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ShoppingBag,
  Plus,
  Search,
  Filter,
  Edit2,
  Trash2,
  Upload,
  Download,
  RefreshCw,
  Package,
  AlertCircle,
  CheckCircle,
  X,
  Image as ImageIcon,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import SkeletonLoader from '@/components/ui/SkeletonLoader';
import Modal from '@/components/ui/Modal';
import {
  listProducts,
  createProduct,
  updateProduct,
  deleteProduct,
  bulkUploadProducts,
} from '@/lib/api';
import { Product, CreateProductData, UpdateProductData } from '@/lib/types';

const PAGE_SIZE = 15;

export default function CataloguePage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [page, setPage] = useState(1);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isBulkModalOpen, setIsBulkModalOpen] = useState(false);
  const [currentProduct, setCurrentProduct] = useState<Product | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const [formData, setFormData] = useState<CreateProductData>({
    name: '',
    description: '',
    price: 0,
    currency: 'USD',
    sku: '',
    stock_quantity: 0,
    category: '',
    is_active: true,
  });

  useEffect(() => {
    fetchProducts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [categoryFilter]);

  // Reset to page 1 whenever filters change
  useEffect(() => {
    setPage(1);
  }, [searchQuery, categoryFilter]);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const res = await listProducts({
        q: searchQuery,
        category: categoryFilter === 'All' ? '' : categoryFilter,
      });
      const items = Array.isArray(res) ? res : (res as { items: Product[] })?.items || [];
      setProducts(items);
    } catch {
      showNotification('error', 'Failed to load products');
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  const showNotification = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 5000);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchProducts();
  };

  const handleAddProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createProduct(formData);
      showNotification('success', 'Product created successfully');
      setIsAddModalOpen(false);
      resetForm();
      fetchProducts();
    } catch {
      showNotification('error', 'Failed to create product');
    }
  };

  const handleUpdateProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentProduct) return;
    try {
      await updateProduct(currentProduct.id, formData as UpdateProductData);
      showNotification('success', 'Product updated successfully');
      setIsEditModalOpen(false);
      resetForm();
      fetchProducts();
    } catch {
      showNotification('error', 'Failed to update product');
    }
  };

  const handleDeleteProduct = async (id: string) => {
    if (!confirm('Are you sure you want to delete this product?')) return;
    try {
      await deleteProduct(id);
      showNotification('success', 'Product deleted');
      fetchProducts();
    } catch {
      showNotification('error', 'Failed to delete product');
    }
  };

  const openEditModal = (product: Product) => {
    setCurrentProduct(product);
    setFormData({
      name: product.name,
      description: product.description || '',
      price: product.price,
      currency: product.currency,
      sku: product.sku,
      stock_quantity: product.stock_quantity,
      category: product.category || '',
      is_active: product.is_active,
    });
    setIsEditModalOpen(true);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      price: 0,
      currency: 'USD',
      sku: '',
      stock_quantity: 0,
      category: '',
      is_active: true,
    });
    setCurrentProduct(null);
  };

  const handleBulkUpload = async (file: File) => {
    try {
      const res = await bulkUploadProducts(file);
      showNotification('success', `Imported ${res.imported} and updated ${res.updated} products`);
      setIsBulkModalOpen(false);
      fetchProducts();
    } catch {
      showNotification('error', 'Failed to upload CSV');
    }
  };

  const categories = ['All', ...Array.from(new Set(products.map((p) => p.category).filter(Boolean)))];

  const totalPages = Math.max(1, Math.ceil(products.length / PAGE_SIZE));
  const pagedProducts = products.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-[var(--brand-primary)]/10 rounded-[var(--radius-squircle)]">
            <ShoppingBag className="w-8 h-8 text-[var(--brand-primary)]" />
          </div>
          <div>
            <h1 className="text-h1 text-[var(--text-primary)]">Product Catalogue</h1>
            <p className="text-body text-[var(--text-secondary)] mt-1">
              Manage your products for the Sales Sub-Agent
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" onClick={() => setIsBulkModalOpen(true)}>
            <Upload className="w-4 h-4 mr-2" />
            Bulk Import
          </Button>
          <Button variant="primary" onClick={() => { resetForm(); setIsAddModalOpen(true); }}>
            <Plus className="w-4 h-4 mr-2" />
            Add Product
          </Button>
        </div>
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

      {/* Filters & Search */}
      <Card className="p-4">
        <div className="flex flex-col md:flex-row gap-4">
          <form onSubmit={handleSearch} className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-tertiary)]" />
            <Input
              placeholder="Search by name, SKU, or category..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </form>
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-[var(--text-tertiary)]" />
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="bg-[var(--bg-primary)] border border-[var(--border-subtle)] rounded-[var(--radius-md)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--brand-primary)]"
            >
              {categories.map((cat) => (
                <option key={cat} value={cat}>{cat || 'Uncategorized'}</option>
              ))}
            </select>
            <Button variant="secondary" size="sm" onClick={fetchProducts}>
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>
      </Card>

      {/* Products Table */}
      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[var(--bg-secondary)] border-b border-[var(--border-subtle)]">
                <th className="px-6 py-4 text-xs font-semibold text-[var(--text-tertiary)] uppercase tracking-wider">Product</th>
                <th className="px-6 py-4 text-xs font-semibold text-[var(--text-tertiary)] uppercase tracking-wider">SKU</th>
                <th className="px-6 py-4 text-xs font-semibold text-[var(--text-tertiary)] uppercase tracking-wider">Category</th>
                <th className="px-6 py-4 text-xs font-semibold text-[var(--text-tertiary)] uppercase tracking-wider">Price</th>
                <th className="px-6 py-4 text-xs font-semibold text-[var(--text-tertiary)] uppercase tracking-wider">Stock</th>
                <th className="px-6 py-4 text-xs font-semibold text-[var(--text-tertiary)] uppercase tracking-wider">Status</th>
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
              ) : pagedProducts.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center">
                    <Package className="w-12 h-12 text-[var(--text-tertiary)] mx-auto mb-3 opacity-20" />
                    <p className="text-[var(--text-secondary)]">No products found</p>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="mt-2"
                      onClick={() => { resetForm(); setIsAddModalOpen(true); }}
                    >
                      Add your first product
                    </Button>
                  </td>
                </tr>
              ) : (
                pagedProducts.map((product) => (
                  <tr key={product.id} className="hover:bg-[var(--bg-secondary)]/50 transition-colors group">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="relative w-10 h-10 rounded-md bg-[var(--bg-tertiary)] flex items-center justify-center overflow-hidden flex-shrink-0">
                          {product.image_urls?.[0] ? (
                            <NextImage src={product.image_urls[0]} alt={product.name} fill className="object-cover" />
                          ) : (
                            <ImageIcon className="w-5 h-5 text-[var(--text-tertiary)]" />
                          )}
                        </div>
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-[var(--text-primary)] truncate">{product.name}</p>
                          <p className="text-xs text-[var(--text-tertiary)] truncate max-w-[200px]">{product.description}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-[var(--text-secondary)] font-mono">{product.sku}</td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-[var(--bg-tertiary)] text-[var(--text-secondary)]">
                        {product.category || 'None'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm font-semibold text-[var(--text-primary)]">
                      {product.currency} {Number(product.price).toFixed(2)}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`text-sm ${product.stock_quantity <= 5 ? 'text-red-500 font-bold' : 'text-[var(--text-secondary)]'}`}>
                        {product.stock_quantity}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                        product.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                      }`}>
                        {product.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <Button variant="ghost" size="sm" onClick={() => openEditModal(product)}>
                          <Edit2 className="w-4 h-4" />
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => handleDeleteProduct(product.id)} className="text-red-500 hover:text-red-700">
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {!loading && products.length > PAGE_SIZE && (
          <div className="px-6 py-4 border-t border-[var(--border-subtle)] flex items-center justify-between">
            <p className="text-sm text-[var(--text-secondary)]">
              Showing {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, products.length)} of {products.length} products
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
                {page} / {totalPages}
              </span>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        )}
      </Card>

      {/* Add/Edit Modal */}
      <Modal
        isOpen={isAddModalOpen || isEditModalOpen}
        onClose={() => { setIsAddModalOpen(false); setIsEditModalOpen(false); resetForm(); }}
        title={isEditModalOpen ? 'Edit Product' : 'Add New Product'}
      >
        <form onSubmit={isEditModalOpen ? handleUpdateProduct : handleAddProduct} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="block text-sm font-medium mb-1">Product Name *</label>
              <Input
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g. Premium Solar Panel"
              />
            </div>
            <div className="col-span-1">
              <label className="block text-sm font-medium mb-1">SKU *</label>
              <Input
                required
                value={formData.sku}
                onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                placeholder="SOL-001"
              />
            </div>
            <div className="col-span-1">
              <label className="block text-sm font-medium mb-1">Category</label>
              <Input
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                placeholder="Solar"
              />
            </div>
            <div className="col-span-1">
              <label className="block text-sm font-medium mb-1">Price *</label>
              <Input
                required
                type="number"
                step="0.01"
                value={formData.price}
                onChange={(e) => setFormData({ ...formData, price: parseFloat(e.target.value) })}
              />
            </div>
            <div className="col-span-1">
              <label className="block text-sm font-medium mb-1">Stock Quantity</label>
              <Input
                type="number"
                value={formData.stock_quantity}
                onChange={(e) => setFormData({ ...formData, stock_quantity: parseInt(e.target.value) })}
              />
            </div>
            <div className="col-span-2">
              <label className="block text-sm font-medium mb-1">Description</label>
              <textarea
                className="w-full bg-[var(--bg-primary)] border border-[var(--border-subtle)] rounded-[var(--radius-md)] px-4 py-3 text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--brand-primary)]"
                rows={3}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Brief description of the product..."
              />
            </div>
            <div className="col-span-2 flex items-center gap-2">
              <input
                type="checkbox"
                id="is_active"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                className="w-4 h-4 text-[var(--brand-primary)] rounded focus:ring-[var(--brand-primary)]"
              />
              <label htmlFor="is_active" className="text-sm font-medium cursor-pointer">
                Product is active and visible to AI
              </label>
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-4 border-t border-[var(--border-subtle)]">
            <Button variant="secondary" type="button" onClick={() => { setIsAddModalOpen(false); setIsEditModalOpen(false); resetForm(); }}>
              Cancel
            </Button>
            <Button variant="primary" type="submit">
              {isEditModalOpen ? 'Save Changes' : 'Create Product'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Bulk Import Modal */}
      <Modal
        isOpen={isBulkModalOpen}
        onClose={() => setIsBulkModalOpen(false)}
        title="Bulk Import Products"
      >
        <div className="space-y-6">
          <div className="p-4 bg-blue-50 border border-blue-100 rounded-[var(--radius-md)]">
            <h4 className="text-sm font-bold text-blue-800 mb-1 flex items-center">
              <AlertCircle className="w-4 h-4 mr-2" />
              CSV Format Instructions
            </h4>
            <p className="text-xs text-blue-700">
              Your CSV should include headers:{' '}
              <code className="bg-blue-100 px-1 rounded">name, price, sku, description, category, stock_quantity</code>.
              SKU is used to identify existing products for updates.
            </p>
            <button className="text-xs font-bold text-blue-800 underline mt-2 flex items-center hover:text-blue-900">
              <Download className="w-3 h-3 mr-1" />
              Download Template CSV
            </button>
          </div>

          <label className="block border-2 border-dashed border-[var(--border-subtle)] rounded-[var(--radius-md)] p-12 text-center hover:border-[var(--brand-primary)] transition-colors cursor-pointer group">
            <input
              type="file"
              accept=".csv"
              className="hidden"
              onChange={(e) => {
                if (e.target.files?.[0]) handleBulkUpload(e.target.files[0]);
              }}
            />
            <Upload className="w-12 h-12 text-[var(--text-tertiary)] mx-auto mb-4 group-hover:text-[var(--brand-primary)]" />
            <p className="text-sm font-medium text-[var(--text-primary)]">Click to upload or drag and drop</p>
            <p className="text-xs text-[var(--text-tertiary)] mt-1">Only .CSV files are supported</p>
          </label>
        </div>
      </Modal>
    </div>
  );
}
