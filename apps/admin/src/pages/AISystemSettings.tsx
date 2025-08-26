import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../api/client";

// Используем any, так как точные структуры могут меняться
type Provider = any;
type Model = any;
type Price = any;

type Defaults = {
  provider_id?: string | null;
  model_id?: string | null;
  bundle_id?: string | null;
};

export default function AISystemSettings() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">AI System Settings</h1>
      <SettingsTab />
    </div>
  );
}

function SettingsTab() {
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

  const [providerDraft, setProviderDraft] = useState<Partial<Provider>>({});
  const [modelDraft, setModelDraft] = useState<Partial<Model>>({});
  const [priceDraft, setPriceDraft] = useState<Partial<Price>>({});

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

  const saveProvider = async () => {
    if (providerDraft.id) {
      await api.put(
        `/admin/ai/system/providers/${encodeURIComponent(providerDraft.id)}`,
        providerDraft,
      );
    } else {
      await api.post("/admin/ai/system/providers", providerDraft);
    }
    setProviderDraft({});
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

  const saveModel = async () => {
    if (modelDraft.id) {
      await api.put(
        `/admin/ai/system/models/${encodeURIComponent(modelDraft.id)}`,
        modelDraft,
      );
    } else {
      await api.post("/admin/ai/system/models", modelDraft);
    }
    setModelDraft({});
    await qc.invalidateQueries({ queryKey: ["ai", "models"] });
  };
  const removeModel = async (id: string) => {
    if (!confirm("Delete model?")) return;
    await api.del(`/admin/ai/system/models/${encodeURIComponent(id)}`);
    await qc.invalidateQueries({ queryKey: ["ai", "models"] });
  };

  const savePrice = async () => {
    if (priceDraft.id) {
      await api.put(
        `/admin/ai/system/prices/${encodeURIComponent(priceDraft.id)}`,
        priceDraft,
      );
    } else {
      await api.post("/admin/ai/system/prices", priceDraft);
    }
    setPriceDraft({});
    await qc.invalidateQueries({ queryKey: ["ai", "prices"] });
  };
  const removePrice = async (id: string) => {
    if (!confirm("Delete price?")) return;
    await api.del(`/admin/ai/system/prices/${encodeURIComponent(id)}`);
    await qc.invalidateQueries({ queryKey: ["ai", "prices"] });
  };

  return (
    <div className="space-y-8">
      <section>
        <h2 className="text-lg font-semibold mb-2">Providers</h2>
        <table className="min-w-full text-sm mb-2">
          <thead>
            <tr className="text-left">
              <th className="p-1">ID</th>
              <th className="p-1">Code</th>
              <th className="p-1">Health</th>
              <th className="p-1">Default</th>
              <th className="p-1">Actions</th>
            </tr>
          </thead>
          <tbody>
            {providers.data?.map((p: any) => (
              <tr key={p.id} className="border-t">
                <td className="p-1">{p.id}</td>
                <td className="p-1">{p.code || p.name}</td>
                <td className="p-1">{p.health || p.health_status || "?"}</td>
                <td className="p-1">
                  {defaults.data?.provider_id === p.id ? (
                    <span className="text-green-600">default</span>
                  ) : (
                    <button
                      className="text-blue-600"
                      onClick={() => setDefaultProvider(p.id)}
                    >
                      make default
                    </button>
                  )}
                </td>
                <td className="p-1 space-x-2">
                  <button
                    className="text-blue-600"
                    onClick={() => setProviderDraft(p)}
                  >
                    edit
                  </button>
                  <button
                    className="text-red-600"
                    onClick={() => removeProvider(p.id)}
                  >
                    del
                  </button>
                  <button
                    className="text-green-600"
                    onClick={() => refreshPrices(p.id)}
                  >
                    refresh prices
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="border rounded p-2 max-w-md space-y-2">
          <h3 className="font-semibold">Edit provider</h3>
          <input
            className="border rounded px-2 py-1 w-full"
            placeholder="code"
            value={providerDraft.code || ""}
            onChange={(e) =>
              setProviderDraft((s) => ({ ...s, code: e.target.value }))
            }
          />
          <input
            className="border rounded px-2 py-1 w-full"
            placeholder="base_url"
            value={providerDraft.base_url || ""}
            onChange={(e) =>
              setProviderDraft((s) => ({ ...s, base_url: e.target.value }))
            }
          />
          <button
            className="px-3 py-1 rounded bg-blue-600 text-white"
            onClick={saveProvider}
          >
            Save
          </button>
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-2">Models</h2>
        <table className="min-w-full text-sm mb-2">
          <thead>
            <tr className="text-left">
              <th className="p-1">ID</th>
              <th className="p-1">Provider</th>
              <th className="p-1">Name</th>
              <th className="p-1">Default</th>
              <th className="p-1">Actions</th>
            </tr>
          </thead>
          <tbody>
            {models.data?.map((m: any) => (
              <tr key={m.id} className="border-t">
                <td className="p-1">{m.id}</td>
                <td className="p-1">{m.provider_id}</td>
                <td className="p-1">{m.name || m.code}</td>
                <td className="p-1">
                  {defaults.data?.model_id === m.id ? (
                    <span className="text-green-600">default</span>
                  ) : (
                    <button
                      className="text-blue-600"
                      onClick={() => setDefaultModel(m.id)}
                    >
                      make default
                    </button>
                  )}
                </td>
                <td className="p-1 space-x-2">
                  <button
                    className="text-blue-600"
                    onClick={() => setModelDraft(m)}
                  >
                    edit
                  </button>
                  <button
                    className="text-red-600"
                    onClick={() => removeModel(m.id)}
                  >
                    del
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="border rounded p-2 max-w-md space-y-2">
          <h3 className="font-semibold">Edit model</h3>
          <input
            className="border rounded px-2 py-1 w-full"
            placeholder="provider_id"
            value={modelDraft.provider_id || ""}
            onChange={(e) =>
              setModelDraft((s) => ({ ...s, provider_id: e.target.value }))
            }
          />
          <input
            className="border rounded px-2 py-1 w-full"
            placeholder="name"
            value={modelDraft.name || ""}
            onChange={(e) =>
              setModelDraft((s) => ({ ...s, name: e.target.value }))
            }
          />
          <button
            className="px-3 py-1 rounded bg-blue-600 text-white"
            onClick={saveModel}
          >
            Save
          </button>
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-2">Prices</h2>
        <button
          className="mb-2 px-2 py-1 rounded bg-green-600 text-white"
          onClick={() => refreshPrices("all")}
        >
          Refresh all prices
        </button>
        <table className="min-w-full text-sm mb-2">
          <thead>
            <tr className="text-left">
              <th className="p-1">ID</th>
              <th className="p-1">Model</th>
              <th className="p-1">Input</th>
              <th className="p-1">Output</th>
              <th className="p-1">Currency</th>
              <th className="p-1">Actions</th>
            </tr>
          </thead>
          <tbody>
            {prices.data?.map((pr: any) => (
              <tr key={pr.id} className="border-t">
                <td className="p-1">{pr.id}</td>
                <td className="p-1">{pr.model_id}</td>
                <td className="p-1">{pr.input_price ?? pr.input_tokens}</td>
                <td className="p-1">{pr.output_price ?? pr.output_tokens}</td>
                <td className="p-1">{pr.currency}</td>
                <td className="p-1 space-x-2">
                  <button
                    className="text-blue-600"
                    onClick={() => setPriceDraft(pr)}
                  >
                    edit
                  </button>
                  <button
                    className="text-red-600"
                    onClick={() => removePrice(pr.id)}
                  >
                    del
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="border rounded p-2 max-w-md space-y-2">
          <h3 className="font-semibold">Edit price</h3>
          <input
            className="border rounded px-2 py-1 w-full"
            placeholder="model_id"
            value={priceDraft.model_id || ""}
            onChange={(e) =>
              setPriceDraft((s) => ({ ...s, model_id: e.target.value }))
            }
          />
          <input
            className="border rounded px-2 py-1 w-full"
            placeholder="input_price"
            value={priceDraft.input_price || priceDraft.input_tokens || ""}
            onChange={(e) =>
              setPriceDraft((s) => ({ ...s, input_price: e.target.value }))
            }
          />
          <input
            className="border rounded px-2 py-1 w-full"
            placeholder="output_price"
            value={priceDraft.output_price || priceDraft.output_tokens || ""}
            onChange={(e) =>
              setPriceDraft((s) => ({ ...s, output_price: e.target.value }))
            }
          />
          <input
            className="border rounded px-2 py-1 w-full"
            placeholder="currency"
            value={priceDraft.currency || ""}
            onChange={(e) =>
              setPriceDraft((s) => ({ ...s, currency: e.target.value }))
            }
          />
          <button
            className="px-3 py-1 rounded bg-blue-600 text-white"
            onClick={savePrice}
          >
            Save
          </button>
        </div>
      </section>
    </div>
  );
}

