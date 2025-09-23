import React from 'react';

type PaginationProps = {
    page: number; // 1-based
    total?: number; // total pages
    hasNext?: boolean;
    onChange: (page: number) => void;
    siblings?: number;
    boundaries?: number;
    className?: string;
};

function range(start: number, end: number): number[] {
    const a: number[] = [];
    for (let i = start; i <= end; i++) a.push(i);
    return a;
}

export function Pagination({
                               page,
                               total,
                               hasNext,
                               onChange,
                               siblings = 1,
                               boundaries = 1,
                               className = ''
                           }: PaginationProps) {
    const hasTotal = typeof total === 'number' && Number.isFinite(total);

    if (hasTotal) {
        const totalPages = Math.max(1, Math.floor(total as number));
        if (totalPages <= 1) return null;
        const startPages = range(1, Math.min(boundaries, totalPages));
        const endPages = range(Math.max(totalPages - boundaries + 1, boundaries + 1), totalPages);
        const siblingStart = Math.max(
            Math.min(page - siblings, totalPages - boundaries - siblings * 2 - 1),
            boundaries + 2,
        );
        const siblingEnd = Math.min(
            Math.max(page + siblings, boundaries + siblings * 2 + 2),
            endPages[0] - 2,
        );

        const items: (number | 'ellipsis')[] = [
            ...startPages,
            ...(siblingStart > boundaries + 2 ? (['ellipsis'] as const) : siblingStart === boundaries + 2 ? [boundaries + 1] : []),
            ...range(siblingStart, siblingEnd),
            ...(siblingEnd < endPages[0] - 1 ? (['ellipsis'] as const) : siblingEnd === endPages[0] - 1 ? [endPages[0] - 1] : []),
            ...endPages,
        ];

        const btnBase = 'min-w-8 h-8 inline-flex items-center justify-center rounded-md text-sm select-none';

        return (
            <div className={`pagination inline-flex items-center gap-1 ${className}`}>
                <button
                    className={`${btnBase} px-2 text-gray-700 hover:bg-gray-100 disabled:opacity-50`}
                    disabled={page <= 1}
                    onClick={() => onChange(Math.max(1, page - 1))}
                >
                    Prev
                </button>
                {items.map((it, idx) =>
                    it === 'ellipsis' ? (
                        <span key={`e${idx}`} className={`${btnBase} text-gray-400`}>...</span>
                    ) : (
                        <button
                            key={it}
                            className={`${btnBase} px-2 ${it === page ? 'bg-primary-600 text-white' : 'text-gray-800 hover:bg-gray-100'}`}
                            onClick={() => onChange(it)}
                        >
                            {it}
                        </button>
                    ),
                )}
                <button
                    className={`${btnBase} px-2 text-gray-700 hover:bg-gray-100 disabled:opacity-50`}
                    disabled={page >= totalPages}
                    onClick={() => onChange(Math.min(totalPages, page + 1))}
                >
                    Next
                </button>
            </div>
        );
    }

    const canPrev = page > 1;
    const canNext = !!hasNext;
    if (!canPrev && !canNext) return null;
    const btnBase = 'min-w-8 h-8 inline-flex items-center justify-center rounded-md text-sm select-none';

    return (
        <div className={`pagination inline-flex items-center gap-2 ${className}`}>
            <button
                className={`${btnBase} px-2 text-gray-700 hover:bg-gray-100 disabled:opacity-50`}
                disabled={!canPrev}
                onClick={() => onChange(Math.max(1, page - 1))}
            >
                Prev
            </button>
            <span className="text-sm text-gray-600">Page {page}</span>
            <button
                className={`${btnBase} px-2 text-gray-700 hover:bg-gray-100 disabled:opacity-50`}
                disabled={!canNext}
                onClick={() => onChange(page + 1)}
            >
                Next
            </button>
        </div>
    );
}

