import React from 'react';

export type TableProps = React.TableHTMLAttributes<HTMLTableElement> & {
    zebra?: boolean;
    hover?: boolean;
};

export function Table({className = '', zebra, hover, children, ...rest}: TableProps) {
    const cls = [
        'table w-full',
        zebra ? 'is-zebra' : '',
        hover ? 'is-hoverable' : '',
        className,
    ]
        .filter(Boolean)
        .join(' ');
    return (
        <table className={cls} {...rest}>
            {children}
        </table>
    );
}

export function THead({className = '', children, ...rest}: React.HTMLAttributes<HTMLTableSectionElement>) {
    return (
        <thead className={`table-thead ${className}`} {...rest}>
        {children}
        </thead>
    );
}

export function TBody({className = '', children, ...rest}: React.HTMLAttributes<HTMLTableSectionElement>) {
    return (
        <tbody className={`table-tbody ${className}`} {...rest}>
        {children}
        </tbody>
    );
}

export function TR({className = '', children, ...rest}: React.HTMLAttributes<HTMLTableRowElement>) {
    return (
        <tr className={`table-tr ${className}`} {...rest}>
            {children}
        </tr>
    );
}

export function TH({className = '', children, ...rest}: React.ThHTMLAttributes<HTMLTableCellElement>) {
    return (
        <th className={`table-th ${className}`} {...rest}>
            {children}
        </th>
    );
}

export function TD({className = '', children, ...rest}: React.TdHTMLAttributes<HTMLTableCellElement>) {
    return (
        <td className={`table-td ${className}`} {...rest}>
            {children}
        </td>
    );
}

export {TablePagination} from './TablePagination';
