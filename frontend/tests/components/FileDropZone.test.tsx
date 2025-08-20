import { render, fireEvent, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import '@testing-library/jest-dom';

// mock react-dropzone so the component's useDropzone works in jsdom
vi.mock('react-dropzone', () => ({
  useDropzone: (opts: any) => {
    const isDisabled = !!(opts && opts.disabled);
    return {
      getRootProps: () => ({
        'data-testid': 'dropzone',
        className: isDisabled ? 'cursor-not-allowed' : '',
        tabIndex: isDisabled ? -1 : 0
      }),
      getInputProps: () => ({
        'data-testid': 'file-input',
        type: 'file',
        // call the onDrop passed to useDropzone when the input changes
        onChange: (e: any) => {
          const files = e.target.files ? Array.from(e.target.files) : [];
          if (opts && typeof opts.onDrop === 'function') {
            opts.onDrop(files);
          }
        }
      }),
      isDragActive: false,
      isDragReject: false
    };
  }
}));

import { FileDropzone } from '../../src/components/upload/FileDropZone';
import { UploadStatus } from '../../src/types/app';

describe('FileDropzone', () => {
    const setup = (props = {}) => {
        const onFileSelect = vi.fn();
        render(
            <FileDropzone
                onFileSelect={onFileSelect}
                uploadStatus={UploadStatus.Idle}
                {...props}
            />
        );
        return { onFileSelect };
    };

    it('renders default UI', () => {
        setup();
        expect(screen.getByText(/Click to upload/i)).toBeInTheDocument();
        expect(screen.getByText(/CSV files only/i)).toBeInTheDocument();
    });

    it('calls onFileSelect when file is dropped', () => {
        const { onFileSelect } = setup();
        const fileInput = screen.getByTestId('file-input') as HTMLInputElement;
        const file = new File(['a,b\n1,2'], 'test.csv', { type: 'text/csv' });
        fireEvent.change(fileInput, { target: { files: [file] } });
        expect(onFileSelect).toHaveBeenCalledWith(file);
    });

    it('shows loading spinner when uploading', () => {
        setup({ uploadStatus: UploadStatus.Uploading });
        expect(screen.getByText(/Uploading your file/i)).toBeInTheDocument();
        expect(document.querySelector('.animate-spin')).toBeInTheDocument();
    });

    it('shows error icon when error', () => {
        setup({ uploadStatus: UploadStatus.Error });
        expect(document.querySelector('svg')).toBeInTheDocument();
        expect(screen.getByText(/Click to upload|Only CSV files are allowed|error/i)).toBeTruthy();
    });

    it('is disabled when disabled prop is true', () => {
        setup({ disabled: true });
        const dropzone = document.querySelector('div[tabindex]') || document.querySelector('div');
        expect(dropzone?.className).toMatch(/cursor-not-allowed/);
    });
});