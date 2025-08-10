import React, { useEffect, useState } from 'react';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

export default function ShadowbotPage() {
  const [account, setAccount] = useState(null);
  const [orders, setOrders] = useState([]);
  const [form, setForm] = useState({ symbol: 'AAPL', qty: 1, side: 'buy', tif: 'day' });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const load = async () => {
    try {
      setError('');
      const [acctRes, ordRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/alpaca/account`),
        fetch(`${API_BASE_URL}/api/alpaca/orders?limit=20`),
      ]);
      if (acctRes.ok) setAccount(await acctRes.json());
      if (ordRes.ok) setOrders((await ordRes.json()).orders || []);
    } catch (e) {
      setError('Unable to reach trading API.');
    }
  };

  useEffect(() => { load(); }, []);

  const placeOrder = async () => {
    if (!form.symbol || form.qty <= 0) return;
    try {
      setSubmitting(true);
      setError('');
      const res = await fetch(`${API_BASE_URL}/api/alpaca/order`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol: form.symbol.trim().toUpperCase(),
          qty: Number(form.qty),
          side: form.side,
          tif: form.tif
        })
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || 'Order failed');
      }
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-6">
      <h1 className="text-2xl font-semibold mb-2">Shadowbot</h1>
      <p className="text-sm text-gray-400 mb-6">Automated trading bot (Alpaca {account?.paper ? 'Paper' : 'Live'})</p>

      {error && (
        <div className="mb-4 p-3 border border-red-700 bg-red-900/20 rounded-lg text-red-300">{error}</div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="panel p-4 lg:col-span-1">
          <h2 className="font-medium mb-3">Account</h2>
          {account ? (
            <ul className="text-sm space-y-1">
              <li><span className="text-gray-400">Status:</span> {account.status}</li>
              <li><span className="text-gray-400">Buying Power:</span> ${account.buying_power}</li>
              <li><span className="text-gray-400">Equity:</span> ${account.equity}</li>
              <li><span className="text-gray-400">Mode:</span> {account.paper ? 'Paper' : 'Live'}</li>
            </ul>
          ) : (
            <p className="text-sm text-gray-500">Connect Alpaca in server env to view account.</p>
          )}
        </div>

        <div className="panel p-4 lg:col-span-1">
          <h2 className="font-medium mb-3">Place Market Order</h2>
          <div className="space-y-3">
            <input className="w-full bg-gray-800 border border-gray-700 rounded-md px-3 py-2" placeholder="Symbol" value={form.symbol} onChange={e => setForm({ ...form, symbol: e.target.value })} />
            <input className="w-full bg-gray-800 border border-gray-700 rounded-md px-3 py-2" placeholder="Quantity" type="number" min="1" value={form.qty} onChange={e => setForm({ ...form, qty: e.target.value })} />
            <div className="flex gap-2">
              <select className="flex-1 bg-gray-800 border border-gray-700 rounded-md px-3 py-2" value={form.side} onChange={e => setForm({ ...form, side: e.target.value })}>
                <option value="buy">Buy</option>
                <option value="sell">Sell</option>
              </select>
              <select className="flex-1 bg-gray-800 border border-gray-700 rounded-md px-3 py-2" value={form.tif} onChange={e => setForm({ ...form, tif: e.target.value })}>
                <option value="day">DAY</option>
                <option value="gtc">GTC</option>
              </select>
            </div>
            <button disabled={submitting} onClick={placeOrder} className="btn-primary w-full py-2 rounded-md disabled:opacity-50">{submitting ? 'Submitting...' : 'Submit Order'}</button>
          </div>
        </div>

        <div className="panel p-4 lg:col-span-1">
          <div className="flex items-center justify-between mb-2">
            <h2 className="font-medium">Recent Orders</h2>
            <button onClick={load} className="text-sm text-blue-400 hover:text-blue-300">Refresh</button>
          </div>
          <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
            {orders.length === 0 ? (
              <p className="text-sm text-gray-500">No recent orders.</p>
            ) : orders.map((o) => (
              <div key={o.id} className="bg-gray-800/40 border border-gray-700 rounded-md px-3 py-2 text-sm flex items-center justify-between">
                <div>
                  <div className="font-mono">{o.symbol} · {o.side.toUpperCase()} · {o.qty}</div>
                  <div className="text-gray-400 text-xs">{o.submitted_at || ''}</div>
                </div>
                <div className="text-xs px-2 py-1 rounded-md border border-gray-600">{o.status}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}


