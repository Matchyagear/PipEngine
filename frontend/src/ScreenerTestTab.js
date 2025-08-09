import React, { useCallback, useMemo, useState } from 'react';

// Lightweight, no-API custom screener UI with basic drag-and-drop to order criteria.
// This only manages UI state; no backend calls are made.

const defaultCriteria = [
  { id: 'price', label: 'Price ($)', type: 'range', value: [5, 200], min: 0, max: 1000, step: 1 },
  { id: 'volume', label: 'Avg Volume (min)', type: 'number', value: 500000, min: 0, step: 1000 },
  { id: 'marketCap', label: 'Market Cap (min, $B)', type: 'number', value: 2, min: 0, step: 0.1 },
  { id: 'sector', label: 'Sector', type: 'multiselect', value: [], options: ['Technology','Healthcare','Financial Services','Energy','Industrials','Consumer Discretionary','Consumer Staples','Utilities','Materials','Real Estate','Communication Services'] },
  { id: 'rsi', label: 'RSI', type: 'range', value: [20, 80], min: 0, max: 100, step: 1 },
  { id: 'smaCross', label: '50MA > 200MA', type: 'boolean', value: false },
];

const CriterionRow = ({ item, index, onDragStart, onDragOver, onDrop, onChange }) => {
  return (
    <div
      draggable
      onDragStart={(e) => onDragStart(e, index)}
      onDragOver={(e) => onDragOver(e, index)}
      onDrop={(e) => onDrop(e, index)}
      className="flex flex-col gap-2 p-3 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800"
    >
      <div className="flex items-center justify-between">
        <div className="font-medium text-gray-900 dark:text-white">{item.label}</div>
        <span className="cursor-grab text-gray-400" title="Drag to reorder">⋮⋮</span>
      </div>

      {item.type === 'range' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2 items-center">
          <div className="flex items-center gap-2">
            <input
              type="number"
              className="w-full border rounded px-2 py-1 bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white"
              value={item.value[0]}
              min={item.min}
              max={item.max}
              step={item.step}
              onChange={(e) => onChange(item.id, [Number(e.target.value), item.value[1]])}
            />
            <span className="text-gray-500">to</span>
            <input
              type="number"
              className="w-full border rounded px-2 py-1 bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white"
              value={item.value[1]}
              min={item.min}
              max={item.max}
              step={item.step}
              onChange={(e) => onChange(item.id, [item.value[0], Number(e.target.value)])}
            />
          </div>
          <input
            type="range"
            min={item.min}
            max={item.max}
            step={item.step}
            value={item.value[0]}
            onChange={(e) => onChange(item.id, [Number(e.target.value), item.value[1]])}
          />
          <input
            type="range"
            min={item.min}
            max={item.max}
            step={item.step}
            value={item.value[1]}
            onChange={(e) => onChange(item.id, [item.value[0], Number(e.target.value)])}
          />
        </div>
      )}

      {item.type === 'number' && (
        <input
          type="number"
          className="w-48 border rounded px-2 py-1 bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white"
          value={item.value}
          min={item.min}
          step={item.step}
          onChange={(e) => onChange(item.id, Number(e.target.value))}
        />
      )}

      {item.type === 'boolean' && (
        <label className="inline-flex items-center gap-2">
          <input
            type="checkbox"
            checked={!!item.value}
            onChange={(e) => onChange(item.id, e.target.checked)}
          />
          <span className="text-gray-700 dark:text-gray-300">Enabled</span>
        </label>
      )}

      {item.type === 'multiselect' && (
        <div className="flex flex-wrap gap-2">
          {item.options.map((opt) => {
            const active = item.value.includes(opt);
            return (
              <button
                key={opt}
                className={`px-2 py-1 rounded border text-sm ${active ? 'bg-blue-600 text-white border-blue-600' : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 border-gray-300 dark:border-gray-600'}`}
                onClick={() => {
                  const next = active ? item.value.filter((v) => v !== opt) : [...item.value, opt];
                  onChange(item.id, next);
                }}
                type="button"
              >
                {opt}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

const ScreenerTestTab = () => {
  const [criteria, setCriteria] = useState(defaultCriteria);
  const [dragIndex, setDragIndex] = useState(null);

  const onDragStart = useCallback((e, index) => {
    setDragIndex(index);
    e.dataTransfer.effectAllowed = 'move';
  }, []);

  const onDragOver = useCallback((e, index) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback((e, index) => {
    e.preventDefault();
    if (dragIndex === null || dragIndex === index) return;
    setCriteria((prev) => {
      const next = [...prev];
      const [moved] = next.splice(dragIndex, 1);
      next.splice(index, 0, moved);
      return next;
    });
    setDragIndex(null);
  }, [dragIndex]);

  const onChange = useCallback((id, value) => {
    setCriteria((prev) => prev.map((c) => (c.id === id ? { ...c, value } : c)));
  }, []);

  const query = useMemo(() => {
    // Produce a normalized filter spec we can later POST to backend
    return criteria.map((c) => ({ id: c.id, value: c.value }));
  }, [criteria]);

  return (
    <div className="h-screen flex flex-col">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-4 mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">Custom Screener (Test)</h1>
            <p className="text-sm text-gray-600 dark:text-gray-400">Reorder criteria by dragging. Adjust values below. No API calls are made yet.</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              className="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
              onClick={() => navigator.clipboard.writeText(JSON.stringify(query))}
            >
              Copy Query JSON
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1">
        <div className="lg:col-span-2 space-y-3 overflow-auto">
          {criteria.map((item, idx) => (
            <CriterionRow
              key={item.id}
              item={item}
              index={idx}
              onDragStart={onDragStart}
              onDragOver={onDragOver}
              onDrop={onDrop}
              onChange={onChange}
            />
          ))}
        </div>

        <div className="space-y-4">
          <div className="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
            <div className="text-sm font-semibold text-gray-900 dark:text-white mb-2">Current Filter JSON</div>
            <pre className="text-xs text-gray-700 dark:text-gray-300 overflow-auto max-h-64 bg-gray-50 dark:bg-gray-900/30 p-3 rounded">
{JSON.stringify(query, null, 2)}
            </pre>
          </div>

          <div className="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
            <div className="text-sm font-semibold text-gray-900 dark:text-white mb-2">Preview (coming soon)</div>
            <p className="text-sm text-gray-600 dark:text-gray-400">We will wire this to a cached backend endpoint later to avoid extra API usage.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScreenerTestTab;


