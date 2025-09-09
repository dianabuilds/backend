import { useEffect, useState } from 'react';

import { api } from '../api/client';
import ListSection from '../components/common/ListSection';
import DataTable from '../components/DataTable';
import type { Column } from '../components/DataTable.helpers';

type RecentTx = {
  id: string;
  user_id: string;
  tariff: string | null;
  amount: number;
  status: string;
};

export default function PaymentsRecent() {
  const [rows, setRows] = useState<RecentTx[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await api.get<RecentTx[]>('/admin/payments/recent', { retry: 1 });
        setRows(Array.isArray(res.data) ? res.data : []);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : 'Ошибка загрузки');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const cols: Column<RecentTx>[] = [
    { key: 'user_id', title: 'User' },
    { key: 'tariff', title: 'Tariff', accessor: (r) => r.tariff || '-' },
    { key: 'amount', title: 'Amount', render: (r) => (r.amount / 100).toFixed(2) },
    {
      key: 'status',
      title: 'Status',
      render: (r) => (
        <span className={/error|fail|refund/i.test(r.status) ? 'text-red-600' : ''}>{r.status}</span>
      ),
    },
  ];

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-lg font-semibold">Payments — Recent</h1>
      <ListSection title="Последние транзакции" loading={loading} error={error}>
        <DataTable<RecentTx>
          columns={cols}
          rows={rows}
          rowKey={(r) => r.id}
          loading={loading}
          emptyText="Нет транзакций"
          rowClassName={(r) => (/error|fail|refund/i.test(r.status) ? 'bg-red-50' : '')}
        />
      </ListSection>
    </div>
  );
}

