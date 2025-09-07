import { useEffect, useMemo, useState } from "react";
import { useAccount } from "../account/AccountContext";
import {
  activateReferralCode,
  deactivateReferralCode,
  exportReferralEventsCSV,
  listReferralCodes,
  listReferralEvents,
  type ReferralCodeAdmin,
  type ReferralEventAdmin,
} from "../api/referrals";
import { useToast } from "../components/ToastProvider";
import { Button, Modal, PageLayout, Table, TextInput } from "../shared/ui";

export default function Referrals() {
  const { addToast } = useToast();
  const [tab, setTab] = useState<"codes" | "events">("codes");

  // Current account (workspace)
  const { accountId } = useAccount();
  const ws = useMemo(() => Math.max(1, Number(accountId) || 1), [accountId]);

  // Filters
  const [ownerUserId, setOwnerUserId] = useState<string>("");
  const [active, setActive] = useState<string>("");
  const [eventsReferrer, setEventsReferrer] = useState<string>("");
  const [dateFrom, setDateFrom] = useState<string>("");
  const [dateTo, setDateTo] = useState<string>("");
  const [eventsLimit, setEventsLimit] = useState<number>(50);
  const [eventsPage, setEventsPage] = useState<number>(0);

  // Data
  const [codes, setCodes] = useState<ReferralCodeAdmin[]>([]);
  const [events, setEvents] = useState<ReferralEventAdmin[]>([]);
  const [loading, setLoading] = useState(false);

  // Reason modal
  const [reasonOpen, setReasonOpen] = useState(false);
  const [reasonText, setReasonText] = useState("");
  const [pendingOwner, setPendingOwner] = useState<string>("");
  const [pendingAction, setPendingAction] = useState<"activate" | "deactivate">("activate");

  const loadCodes = async () => {
    setLoading(true);
    try {
      const data = await listReferralCodes({
        workspace_id: ws,
        owner_user_id: ownerUserId || undefined,
        active: active === "true" ? true : active === "false" ? false : undefined,
        limit: 100,
        offset: 0,
      });
      setCodes(data);
    } catch {
      addToast({ title: "Failed to load codes", variant: "error" });
    } finally {
      setLoading(false);
    }
  };

  const loadEvents = async () => {
    setLoading(true);
    try {
      const data = await listReferralEvents({
        workspace_id: ws,
        referrer_user_id: eventsReferrer || undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        limit: eventsLimit,
        offset: eventsPage * eventsLimit,
      });
      setEvents(data);
    } catch {
      addToast({ title: "Failed to load events", variant: "error" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!accountId) return;
    if (tab === "codes") loadCodes();
    else loadEvents();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, accountId]);

  useEffect(() => {
    if (tab === "events" && accountId) loadEvents();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [eventsPage, eventsLimit]);

  const openReason = (owner: string, action: "activate" | "deactivate") => {
    setPendingOwner(owner);
    setPendingAction(action);
    setReasonText("");
    setReasonOpen(true);
  };

  const confirmReason = async () => {
    try {
      if (pendingAction === "activate") {
        await activateReferralCode(pendingOwner, ws, reasonText || undefined);
        addToast({ title: "Code activated", variant: "success" });
      } else {
        await deactivateReferralCode(pendingOwner, ws, reasonText || undefined);
        addToast({ title: "Code deactivated", variant: "success" });
      }
      setReasonOpen(false);
      await loadCodes();
    } catch {
      addToast({ title: pendingAction === "activate" ? "Activation failed" : "Deactivation failed", variant: "error" });
    }
  };

  const onExportCSV = async () => {
    try {
      const blob = await exportReferralEventsCSV({
        workspace_id: ws,
        referrer_user_id: eventsReferrer || undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        limit: 10000,
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "referral_events.csv";
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      addToast({ title: "Export failed", variant: "error" });
    }
  };

  return (
    <PageLayout
      title="Referrals"
      actions={
        <div className="flex gap-2">
          <Button onClick={() => setTab("codes")} variant={tab === "codes" ? "primary" : "secondary"}>
            Codes
          </Button>
          <Button onClick={() => setTab("events")} variant={tab === "events" ? "primary" : "secondary"}>
            Events
          </Button>
        </div>
      }
    >
      <div className="mb-3 flex flex-wrap items-end gap-2">
        {!accountId && (
          <div className="text-sm text-yellow-700 bg-yellow-50 border border-yellow-200 rounded px-2 py-1">
            Select an account to manage referrals (press Ctrl/Cmd+K)
          </div>
        )}
        {tab === "codes" ? (
          <>
            <div>
              <label className="text-xs text-gray-600">Owner user id</label>
              <TextInput value={ownerUserId} onChange={(e) => setOwnerUserId(e.target.value)} className="w-80" />
            </div>
            <div>
              <label className="text-xs text-gray-600">Active</label>
              <select value={active} onChange={(e) => setActive(e.target.value)} className="border rounded px-2 py-1 text-sm">
                <option value="">any</option>
                <option value="true">true</option>
                <option value="false">false</option>
              </select>
            </div>
            <Button onClick={loadCodes} disabled={loading || !accountId}>Reload</Button>
          </>
        ) : (
          <>
            <div>
              <label className="text-xs text-gray-600">Referrer user id</label>
              <TextInput value={eventsReferrer} onChange={(e) => setEventsReferrer(e.target.value)} className="w-80" />
            </div>
            <div>
              <label className="text-xs text-gray-600">From</label>
              <TextInput type="datetime-local" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
            </div>
            <div>
              <label className="text-xs text-gray-600">To</label>
              <TextInput type="datetime-local" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
            </div>
            <div className="flex items-center gap-2">
              <label className="text-xs text-gray-600">Page size</label>
              <TextInput
                type="number"
                value={eventsLimit}
                onChange={(e) => setEventsLimit(Math.max(1, Math.min(1000, Number(e.target.value) || 1)))}
                className="w-20"
              />
              <Button disabled={eventsPage === 0 || loading} onClick={() => setEventsPage((p) => Math.max(0, p - 1))}>
                ‹ Prev
              </Button>
              <Button disabled={loading || events.length < eventsLimit} onClick={() => setEventsPage((p) => p + 1)}>
                Next ›
              </Button>
              <Button onClick={loadEvents} disabled={loading || !accountId}>Reload</Button>
            </div>
            <Button onClick={onExportCSV} disabled={loading || !accountId}>Export CSV</Button>
          </>
        )}
      </div>

      {tab === "codes" ? (
        <Table className="min-w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="p-2 text-left">Code</th>
              <th className="p-2 text-left">Owner</th>
              <th className="p-2 text-left">Active</th>
              <th className="p-2 text-left">Uses</th>
              <th className="p-2 text-left">Actions</th>
            </tr>
          </thead>
          <tbody>
            {codes.map((c) => (
              <tr key={c.id} className="border-b">
                <td className="p-2 font-mono">{c.code}</td>
                <td className="p-2 font-mono">{c.owner_user_id}</td>
                <td className="p-2">{String(c.active)}</td>
                <td className="p-2">{c.uses_count}</td>
                <td className="p-2">
                  {c.active ? (
                    <Button onClick={() => openReason(c.owner_user_id || "", "deactivate")} size="sm">Deactivate</Button>
                  ) : (
                    <Button onClick={() => openReason(c.owner_user_id || "", "activate")} size="sm">Activate</Button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      ) : (
        <Table className="min-w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="p-2 text-left">Occurred at</th>
              <th className="p-2 text-left">Referrer</th>
              <th className="p-2 text-left">Referee</th>
              <th className="p-2 text-left">Code</th>
              <th className="p-2 text-left">Type</th>
            </tr>
          </thead>
          <tbody>
            {events.map((e) => (
              <tr key={e.id} className="border-b">
                <td className="p-2">{new Date(e.occurred_at).toLocaleString()}</td>
                <td className="p-2 font-mono">{e.referrer_user_id}</td>
                <td className="p-2 font-mono">{e.referee_user_id}</td>
                <td className="p-2 font-mono">{e.code}</td>
                <td className="p-2">{e.event_type}</td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}

      {reasonOpen && (
        <Modal onClose={() => setReasonOpen(false)}>
          <div className="p-4 w-96">
            <h3 className="font-semibold mb-2">{pendingAction === "activate" ? "Activate" : "Deactivate"} code</h3>
            <p className="text-sm mb-2">Owner user id: <span className="font-mono">{pendingOwner}</span></p>
            <label className="text-sm">Reason (optional)</label>
            <TextInput value={reasonText} onChange={(e) => setReasonText(e.target.value)} className="w-full mb-3" />
            <div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={() => setReasonOpen(false)}>Cancel</Button>
              <Button onClick={confirmReason}>Confirm</Button>
            </div>
          </div>
        </Modal>
      )}
    </PageLayout>
  );
}
