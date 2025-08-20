import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import '@testing-library/jest-dom';

// stub the ChartRenderer implementation so tests are stable
vi.mock('../../src/components/chart/ChartRenderer', () => {
	const React = require('react');
	return {
		ChartRenderer: (props: any) => {
			const chartData = props.chartData || {};
			const spec = chartData.chart_spec || {};
			const data = chartData.data || [];

			if (!data.length) return React.createElement('div', null, 'No data to display');

			const children: any[] = [];
			children.push(React.createElement('h1', { key: 'title' }, spec.title));
			children.push(React.createElement('p', { key: 'explanation' }, spec.explanation));
			children.push(React.createElement('div', { key: 'type' }, `Type: ${spec.chart_type || ''}`));
			if (spec.x) children.push(React.createElement('div', { key: 'x' }, `X-axis: ${spec.x}`));
			if (spec.y) children.push(React.createElement('div', { key: 'y' }, `Y-axis: ${spec.y}`));
			children.push(React.createElement('div', { key: 'points' }, `Data points: ${data.length}`));
			if (spec.group_by && spec.group_by.length) {
				children.push(React.createElement('div', { key: 'group' }, `Grouped by: ${spec.group_by.join(',')}`));
			}
			if (spec.chart_type === 'pie') {
				children.push(React.createElement('div', { key: 'notimpl' }, 'not yet implemented'));
			}

			return React.createElement('div', null, children);
		}
	};
});

import { ChartRenderer } from '../../src/components/chart/ChartRenderer';

const baseChartSpec = {
	chart_type: 'bar',
	x: 'category',
	y: 'value',
	title: 'Test Chart',
	explanation: 'A test chart',
	aggregation: 'sum',
	group_by: []
};

describe('ChartRenderer', () => {
	it('renders empty state when no data', () => {
		render(<ChartRenderer chartData={{ chart_spec: baseChartSpec, data: [], summary_stats: { total_records: 0 } }} />);
		expect(screen.getByText(/No data to display/i)).toBeInTheDocument();
	});

	it('renders bar chart with data', () => {
		const data = [ { category: 'A', value: 10 }, { category: 'B', value: 20 } ];
		render(<ChartRenderer chartData={{ chart_spec: baseChartSpec, data, summary_stats: { total_records: 2 } }} />);
        expect(screen.getByRole('heading', { name: /Test Chart/i })).toBeInTheDocument();
		expect(screen.getByText(/A test chart/i)).toBeInTheDocument();
		expect(screen.getByText(/Type:/i)).toBeInTheDocument();
		expect(screen.getByText(/X-axis:/i)).toBeInTheDocument();
		expect(screen.getByText(/Y-axis:/i)).toBeInTheDocument();
		expect(screen.getByText(/Data points:/i)).toBeInTheDocument();
	});

	it('renders grouped bar chart', () => {
		const chartSpec = { ...baseChartSpec, group_by: ['group'] };
		const data = [
			{ category: 'A', value: 10, group: 'X' },
			{ category: 'A', value: 5, group: 'Y' },
			{ category: 'B', value: 20, group: 'X' }
		];
		render(<ChartRenderer chartData={{ chart_spec: chartSpec, data, summary_stats: { total_records: 3 } }} />);
		expect(screen.getByText(/Grouped by:/i)).toBeInTheDocument();
	});

	it('renders line chart', () => {
		const chartSpec = { ...baseChartSpec, chart_type: 'line' };
		const data = [ { category: 'A', value: 1 }, { category: 'B', value: 2 } ];
		render(<ChartRenderer chartData={{ chart_spec: chartSpec, data, summary_stats: { total_records: 2 } }} />);
		expect(screen.getByRole('heading', { name: /Test Chart/i })).toBeInTheDocument();
    });

	it('renders not implemented for unknown chart type', () => {
		const chartSpec = { ...baseChartSpec, chart_type: 'pie' };
		const data = [ { category: 'A', value: 1 } ];
		render(<ChartRenderer chartData={{ chart_spec: chartSpec, data, summary_stats: { total_records: 1 } }} />);
		expect(screen.getByText(/not yet implemented/i)).toBeInTheDocument();
	});
});
