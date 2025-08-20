
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ChatService } from '../../src/services/chat.service';
import ApiService from "../../src/services/api.service";

vi.mock('@/services/api.service');

describe('ChatService', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('should ask question', async () => {
		(ApiService.post as any).mockResolvedValue({ data: { answer: '42' }, success: true });
		const req = { file_id: '1', question: 'What?' };
		const res = await ChatService.askQuestion(req as any);
		expect(res.success).toBe(true);
		expect(ApiService.post).toHaveBeenCalledWith('/chat/ask', req);
	});

	it('should validate chart', async () => {
		(ApiService.post as any).mockResolvedValue({ data: { valid: true }, success: true });
		const chartSpec = { chart_type: 'bar' };
		const fileId = 'abc';
		const res = await ChatService.validateChart(chartSpec, fileId);
		expect(res.success).toBe(true);
		expect(ApiService.post).toHaveBeenCalledWith(`/chat/validate-chart?file_id=${fileId}`, chartSpec);
	});

	it('should generate suggested questions (numeric/date/categorical)', () => {
		const colInfo = { date: 'date', amount: 'float', category: 'string' };
		const suggestions = ChatService.generateSuggestedQuestions(colInfo);
		expect(Array.isArray(suggestions)).toBe(true);
		expect(suggestions.length).toBeGreaterThan(0);
	});

	it('should generate fallback suggestions', () => {
		const colInfo = { foo: 'unknown' };
		const suggestions = ChatService.generateSuggestedQuestions(colInfo);
		expect(suggestions.some(s => s.includes('summary'))).toBe(true);
	});

	it('should format chart data for recharts (pie)', () => {
		const chartData = {
			chart_spec: { chart_type: 'pie', x: 'cat', y: 'val', title: 'Pie' },
			data: [ { cat: 'A', val: 10 }, { cat: 'B', val: 20 } ]
		};
		const formatted = ChatService.formatChartDataForRecharts(chartData as any);
		expect(formatted.data[0]).toHaveProperty('name');
		expect(formatted.data[0]).toHaveProperty('value');
	});

	it('should format chart data for recharts (bar)', () => {
		const chartData = {
			chart_spec: { chart_type: 'bar', x: 'cat', y: 'val', title: 'Bar' },
			data: [ { cat: 'A', val: 10 } ]
		};
		const formatted = ChatService.formatChartDataForRecharts(chartData as any);
		expect(formatted.data[0].cat).toBe('A');
	});

	it('should format chart data for recharts (scatter)', () => {
		const chartData = {
			chart_spec: { chart_type: 'scatter', x: 'x', y: 'y', title: 'Scatter' },
			data: [ { x: 1, y: 2 } ]
		};
		const formatted = ChatService.formatChartDataForRecharts(chartData as any);
		expect(formatted.data[0].x).toBe(1);
		expect(formatted.data[0].y).toBe(2);
	});
});
