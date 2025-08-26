import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import {
  Cloud,
  Box,
  Wallet,
  Pencil,
  Trash2,
  RefreshCcw,
  Plus,
  Search,
  Circle,
} from "lucide-react";

import { api } from "../api/client";
import DataTable from "../components/DataTable";
import type { Column } from "../components/DataTable.helpers";
import TabRouter from "../components/TabRouter";
import Slideover from "../components/Slideover";

// Используем any, так как точные структуры могут меняться
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Provider = any;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Model = any;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Price = any;

interface Defaults {
  provider_id?: string | null;
  model_id?: string | null;
  bundle_id?: string | null;
}

export default function AISystemSettings() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">AI System Settings</h1>
      <SettingsTabs />
    </div>
  );
}

function StatusDot({ status }: { status?: string }) {
  const s = (status || "").toLowerCase();
  let color = "text-gray-400";
  if (s.includes("ok") || s.includes("up") || s.includes("healthy")) {
    color = "text-green-500";
  } else if (s.includes("warn") || s.includes("degraded")) {
    color = "text-yellow-500";
  } else if (s.includes("down") || s.includes("error")) {
    color = "text-red-500";
  }
  return <Circle className={`w-3 h-3 ${color}`} fill="currentColor" />;
}

function SettingsTabs() {
  const qc = useQueryClient();
  const providers = useQuery({
    queryKey: ["ai", "providers"],
    queryFn: async () =>
      (await api.get<Provider[]>("/admin/ai/system/providers")).data || [],
  });
  const models = useQuery({
    queryKey: ["ai", "models"],
    queryFn: async () =>
      (await api.get<Model[]>("/admin/ai/system/models")).data || [],
  });
  const prices = useQuery({
    queryKey: ["ai", "prices"],
    queryFn: async () =>
      (await api.get<Price[]>("/admin/ai/system/prices")).data || [],
  });
  const defaults = useQuery({
    queryKey: ["ai", "defaults"],
    queryFn: async () =>
      (await api.get<Defaults>("/admin/ai/system/defaults")).data || {},
  });

  // Drafts for editor
  const [providerDraft, setProviderDraft] =
    useState<Partial<Provider> | null>(null);
  const [modelDraft, setModelDraft] = useState<Partial<Model> | null>(null);
  const [priceDraft, setPriceDraft] = useState<Partial<Price> | null>(null);

  // Search / filters
  const [providerSearch, setProviderSearch] = useState("");
  const [modelSearch, setModelSearch] = useState("");
  const [modelProviderFilter, setModelProviderFilter] = useState("");
  const [priceSearch, setPriceSearch] = useState("");

  // Filtered rows
  const providerRows = useMemo(
    () =>
      (providers.data || []).filter((p: Provider) => {
        const term = providerSearch.toLowerCase();
        return [p.id, p.code, p.name]
          .filter(Boolean)
          .some((v) => String(v).toLowerCase().includes(term));
      }),
    [providers.data, providerSearch],
  );
  const modelRows = useMemo(
    () =>
      (models.data || []).filter((m: Model) => {
        const term = modelSearch.toLowerCase();
        if (modelProviderFilter && m.provider_id !== modelProviderFilter) {
          return false;
        }
        return [m.id, m.name, m.code]
          .filter(Boolean)
          .some((v) => String(v).toLowerCase().includes(term));
      }),
    [models.data, modelSearch, modelProviderFilter],
  );
  const priceRows = useMemo(
    () =>
      (prices.data || []).filter((pr: Price) => {
        const term = priceSearch.toLowerCase();
        return [pr.id, pr.model_id, pr.currency]
          .filter(Boolean)
          .some((v) => String(v).toLowerCase().includes(term));
      }),
    [prices.data, priceSearch],
  );

  // Default setters
  const setDefaultProvider = async (id: string) => {
    await api.put("/admin/ai/system/defaults", {
      ...(defaults.data || {}),
      provider_id: id,
    });
    await qc.invalidateQueries({ queryKey: ["ai", "defaults"] });
  };
  const setDefaultModel = async (id: string) => {
    await api.put("/admin/ai/system/defaults", {
      ...(defaults.data || {}),
      model_id: id,
    });
    await qc.invalidateQueries({ queryKey: ["ai", "defaults"] });
  };

  // Provider actions
  const saveProvider = async () => {
    if (!providerDraft) return;
    if (providerDraft.id) {
      await api.put(
        `/admin/ai/system/providers/${encodeURIComponent(providerDraft.id)}`,
        providerDraft,
      );
    } else {
      await api.post("/admin/ai/system/providers", providerDraft);
    }
    setProviderDraft(null);
    await qc.invalidateQueries({ queryKey: ["ai", "providers"] });
  };
  const removeProvider = async (id: string) => {
    if (!confirm("Delete provider?")) return;
    await api.del(`/admin/ai/system/providers/${encodeURIComponent(id)}`);
    await qc.invalidateQueries({ queryKey: ["ai", "providers"] });
  };
  const refreshPrices = async (id: string) => {
    await api.post(
      `/admin/ai/system/providers/${encodeURIComponent(id)}/refresh_prices`,
      {},
    );
    await qc.invalidateQueries({ queryKey: ["ai", "prices"] });
  };

  // Model actions
  const saveModel = async () => {
    if (!modelDraft) return;
    if (modelDraft.id) {
      await api.put(
        `/admin/ai/system/models/${encodeURIComponent(modelDraft.id)}`,
        modelDraft,
      );
    } else {
      await api.post("/admin/ai/system/models", modelDraft);
    }
    setModelDraft(null);
    await qc.invalidateQueries({ queryKey: ["ai", "models"] });
  };
  const removeModel = async (id: string) => {
    if (!confirm("Delete model?")) return;
    await api.del(`/admin/ai/system/models/${encodeURIComponent(id)}`);
    await qc.invalidateQueries({ queryKey: ["ai", "models"] });
  };

  // Price actions
  const savePrice = async () => {
    if (!priceDraft) return;
    if (priceDraft.id) {
      await api.put(
        `/admin/ai/system/prices/${encodeURIComponent(priceDraft.id)}`,
        priceDraft,
      );
    } else {
      await api.post("/admin/ai/system/prices", priceDraft);
    }
    setPriceDraft(null);
    await qc.invalidateQueries({ queryKey: ["ai", "prices"] });
  };
  const removePrice = async (id: string) => {
    if (!confirm("Delete price?")) return;
    await api.del(`/admin/ai/system/prices/${encodeURIComponent(id)}`);
    await qc.invalidateQueries({ queryKey: ["ai", "prices"] });
  };

  const providerColumns: Column<Provider>[] = [
    { key: "id", title: "ID" },
    { key: "code", title: "Code" },
    {
      key: "health",
      title: "Health",
      render: (p) => <StatusDot status={p.health || p.health_status} />,
    },
    {
      key: "default",
      title: "Default",
      render: (p) =>
        defaults.data?.provider_id === p.id ? (
          <span className="text-green-600">default</span>
        ) : (
          <button
            className="text-blue-600"
            onClick={() => setDefaultProvider(p.id)}
          >
            make default
          </button>
        ),
    },
    {
      key: "actions",
      title: "Actions",
      render: (p) => (
        <div className="flex gap-2">
          <button
            className="text-blue-600"
            onClick={() => setProviderDraft(p)}
          >
            <Pencil className="w-4 h-4" />
          </button>
          <button
            className="text-red-600"
            onClick={() => removeProvider(p.id)}
          >
            <Trash2 className="w-4 h-4" />
          </button>
          <button
            className="text-green-600"
            onClick={() => refreshPrices(p.id)}
          >
            <RefreshCcw className="w-4 h-4" />
          </button>
        </div>
      ),
    },
  ];

  const modelColumns: Column<Model>[] = [
    { key: "id", title: "ID" },
    {
      key: "provider",
      title: "Provider",
      render: (m) =>
        providers.data?.find((p: Provider) => p.id === m.provider_id)?.code ||
        m.provider_id,
    },
    { key: "name", title: "Name", accessor: (m) => m.name || m.code },
    {
      key: "default",
      title: "Default",
      render: (m) =>
        defaults.data?.model_id === m.id ? (
          <span className="text-green-600">default</span>
        ) : (
          <button
            className="text-blue-600"
            onClick={() => setDefaultModel(m.id)}
          >
            make default
          </button>
        ),
    },
    {
      key: "actions",
      title: "Actions",
      render: (m) => (
        <div className="flex gap-2">
          <button className="text-blue-600" onClick={() => setModelDraft(m)}>
            <Pencil className="w-4 h-4" />
          </button>
          <button
            className="text-red-600"
            onClick={() => removeModel(m.id)}
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      ),
    },
  ];

  const priceColumns: Column<Price>[] = [
    { key: "id", title: "ID" },
    {
      key: "model",
      title: "Model",
      render: (pr) =>
        models.data?.find((m: Model) => m.id === pr.model_id)?.name ||
        pr.model_id,
    },
    {
      key: "input",
      title: "Input",
      accessor: (pr) => pr.input_price ?? pr.input_tokens,
    },
    {
      key: "output",
      title: "Output",
      accessor: (pr) => pr.output_price ?? pr.output_tokens,
    },
    { key: "currency", title: "Currency" },
    {
      key: "actions",
      title: "Actions",
      render: (pr) => (
        <div className="flex gap-2">
          <button className="text-blue-600" onClick={() => setPriceDraft(pr)}>
            <Pencil className="w-4 h-4" />
          </button>
          <button
            className="text-red-600"
            onClick={() => removePrice(pr.id)}
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      ),
    },
  ];

  return (
    <TabRouter
      plugins={[
        {
          name: "Providers",
          render: () => (
            <div className="space-y-4">
              <div className="bg-white p-4 rounded shadow space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-lg font-semibold">
                    <Cloud className="w-5 h-5" />
                    Providers
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="relative">
                      <Search className="w-4 h-4 absolute left-2 top-1/2 -translate-y-1/2 text-gray-400" />
                      <input
                        className="border rounded pl-6 pr-2 py-1"
                        placeholder="Search..."
                        value={providerSearch}
                        onChange={(e) => setProviderSearch(e.target.value)}
                      />
                    </div>
                    <button
                      className="flex items-center gap-1 px-2 py-1 rounded bg-blue-600 text-white"
                      onClick={() => setProviderDraft({})}
                    >
                      <Plus className="w-4 h-4" /> Add
                    </button>
                  </div>
                </div>
                <DataTable
                  columns={providerColumns}
                  rows={providerRows}
                  rowKey={(p) => String(p.id)}
                  rowClassName="odd:bg-gray-50"
                />
              </div>
              <Slideover
                open={!!providerDraft}
                title={providerDraft?.id ? "Edit provider" : "New provider"}
                onClose={() => setProviderDraft(null)}
              >
                <div className="space-y-2">
                  <div className="flex flex-col gap-1">
                    <label className="text-sm text-gray-600">code</label>
                    <input
                      className="border rounded px-2 py-1 w-full"
                      value={providerDraft?.code || ""}
                      onChange={(e) =>
                        setProviderDraft((s) => ({ ...(s || {}), code: e.target.value }))
                      }
                    />
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="text-sm text-gray-600">base_url</label>
                    <input
                      className="border rounded px-2 py-1 w-full"
                      value={providerDraft?.base_url || ""}
                      onChange={(e) =>
                        setProviderDraft((s) => ({ ...(s || {}), base_url: e.target.value }))
                      }
                    />
                  </div>
                  <button
                    className="px-3 py-1 rounded bg-blue-600 text-white"
                    onClick={saveProvider}
                  >
                    Save
                  </button>
                </div>
              </Slideover>
            </div>
          ),
        },
        {
          name: "Models",
          render: () => (
            <div className="space-y-4">
              <div className="bg-white p-4 rounded shadow space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-lg font-semibold">
                    <Box className="w-5 h-5" />
                    Models
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="relative">
                      <Search className="w-4 h-4 absolute left-2 top-1/2 -translate-y-1/2 text-gray-400" />
                      <input
                        className="border rounded pl-6 pr-2 py-1"
                        placeholder="Search..."
                        value={modelSearch}
                        onChange={(e) => setModelSearch(e.target.value)}
                      />
                    </div>
                    <select
                      className="border rounded px-2 py-1"
                      value={modelProviderFilter}
                      onChange={(e) => setModelProviderFilter(e.target.value)}
                    >
                      <option value="">All providers</option>
                      {providers.data?.map((p: Provider) => (
                        <option key={p.id} value={p.id}>
                          {p.code || p.name}
                        </option>
                      ))}
                    </select>
                    <button
                      className="flex items-center gap-1 px-2 py-1 rounded bg-blue-600 text-white"
                      onClick={() => setModelDraft({})}
                    >
                      <Plus className="w-4 h-4" /> Add
                    </button>
                  </div>
                </div>
                <DataTable
                  columns={modelColumns}
                  rows={modelRows}
                  rowKey={(m) => String(m.id)}
                  rowClassName="odd:bg-gray-50"
                />
              </div>
              <Slideover
                open={!!modelDraft}
                title={modelDraft?.id ? "Edit model" : "New model"}
                onClose={() => setModelDraft(null)}
              >
                <div className="space-y-2">
                  <div className="flex flex-col gap-1">
                    <label className="text-sm text-gray-600">provider</label>
                    <select
                      className="border rounded px-2 py-1 w-full"
                      value={modelDraft?.provider_id || ""}
                      onChange={(e) =>
                        setModelDraft((s) => ({ ...(s || {}), provider_id: e.target.value }))
                      }
                    >
                      <option value="">Select provider</option>
                      {providers.data?.map((p: Provider) => (
                        <option key={p.id} value={p.id}>
                          {p.code || p.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="text-sm text-gray-600">name</label>
                    <input
                      className="border rounded px-2 py-1 w-full"
                      value={modelDraft?.name || ""}
                      onChange={(e) =>
                        setModelDraft((s) => ({ ...(s || {}), name: e.target.value }))
                      }
                    />
                  </div>
                  <button
                    className="px-3 py-1 rounded bg-blue-600 text-white"
                    onClick={saveModel}
                  >
                    Save
                  </button>
                </div>
              </Slideover>
            </div>
          ),
        },
        {
          name: "Prices",
          render: () => (
            <div className="space-y-4">
              <div className="bg-white p-4 rounded shadow space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-lg font-semibold">
                    <Wallet className="w-5 h-5" />
                    Prices
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="relative">
                      <Search className="w-4 h-4 absolute left-2 top-1/2 -translate-y-1/2 text-gray-400" />
                      <input
                        className="border rounded pl-6 pr-2 py-1"
                        placeholder="Search..."
                        value={priceSearch}
                        onChange={(e) => setPriceSearch(e.target.value)}
                      />
                    </div>
                    <button
                      className="flex items-center gap-1 px-2 py-1 rounded bg-blue-600 text-white"
                      onClick={() => setPriceDraft({})}
                    >
                      <Plus className="w-4 h-4" /> Add
                    </button>
                    <button
                      className="flex items-center gap-1 px-2 py-1 rounded bg-green-600 text-white"
                      onClick={() => refreshPrices("all")}
                    >
                      <RefreshCcw className="w-4 h-4" /> Refresh
                    </button>
                  </div>
                </div>
                <DataTable
                  columns={priceColumns}
                  rows={priceRows}
                  rowKey={(pr) => String(pr.id)}
                  rowClassName="odd:bg-gray-50"
                />
              </div>
              <Slideover
                open={!!priceDraft}
                title={priceDraft?.id ? "Edit price" : "New price"}
                onClose={() => setPriceDraft(null)}
              >
                <div className="space-y-2">
                  <div className="flex flex-col gap-1">
                    <label className="text-sm text-gray-600">model</label>
                    <select
                      className="border rounded px-2 py-1 w-full"
                      value={priceDraft?.model_id || ""}
                      onChange={(e) =>
                        setPriceDraft((s) => ({ ...(s || {}), model_id: e.target.value }))
                      }
                    >
                      <option value="">Select model</option>
                      {models.data?.map((m: Model) => (
                        <option key={m.id} value={m.id}>
                          {m.name || m.code}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="text-sm text-gray-600">input_price</label>
                    <input
                      className="border rounded px-2 py-1 w-full"
                      value={
                        priceDraft?.input_price ?? priceDraft?.input_tokens ?? ""
                      }
                      onChange={(e) =>
                        setPriceDraft((s) => ({ ...(s || {}), input_price: e.target.value }))
                      }
                    />
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="text-sm text-gray-600">output_price</label>
                    <input
                      className="border rounded px-2 py-1 w-full"
                      value={
                        priceDraft?.output_price ?? priceDraft?.output_tokens ?? ""
                      }
                      onChange={(e) =>
                        setPriceDraft((s) => ({ ...(s || {}), output_price: e.target.value }))
                      }
                    />
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="text-sm text-gray-600">currency</label>
                    <input
                      className="border rounded px-2 py-1 w-full"
                      value={priceDraft?.currency || ""}
                      onChange={(e) =>
                        setPriceDraft((s) => ({ ...(s || {}), currency: e.target.value }))
                      }
                    />
                  </div>
                  <button
                    className="px-3 py-1 rounded bg-blue-600 text-white"
                    onClick={savePrice}
                  >
                    Save
                  </button>
                </div>
              </Slideover>
            </div>
          ),
        },
      ]}
    />
  );
}

