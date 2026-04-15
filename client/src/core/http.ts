const API_BASE = 'http://localhost:8000';

export function buildApiUrl(path: string): string {
    return `${API_BASE}${path}`;
}

async function extractErrorMessage(response: Response): Promise<string> {
    const contentType = response.headers.get('content-type') ?? '';

    if (contentType.includes('application/json')) {
        try {
            const body = (await response.json()) as {
                detail?: unknown;
                message?: unknown;
            };

            if (typeof body.detail === 'string') {
                return body.detail;
            }
            if (typeof body.message === 'string') {
                return body.message;
            }
        } catch {
            // Fall through to a text-based fallback.
        }
    }

    return (await response.text()) || `HTTP ${response.status}`;
}

export async function fetchApi(
    path: string,
    init?: RequestInit,
): Promise<Response> {
    const response = await fetch(buildApiUrl(path), init);

    if (!response.ok) {
        throw new Error(await extractErrorMessage(response));
    }

    return response;
}

export async function getJson<T>(path: string): Promise<T> {
    return (await (await fetchApi(path)).json()) as T;
}

export async function postJson<T>(path: string, body: unknown): Promise<T> {
    return (await (
        await fetchApi(path, {
            method: 'POST',
            headers: { 'content-type': 'application/json' },
            body: JSON.stringify(body),
        })
    ).json()) as T;
}

export async function postFormData<T>(
    path: string,
    formData: FormData,
): Promise<T> {
    return (await (
        await fetchApi(path, {
            method: 'POST',
            body: formData,
        })
    ).json()) as T;
}

export async function deleteRequest(path: string): Promise<void> {
    await fetchApi(path, { method: 'DELETE' });
}

export function createSlicedUploadFile(
    file: File,
    maxBytes = 10 * 1024 * 1024,
): File {
    const isParquet = file.name.toLowerCase().endsWith('.parquet');
    const fileSlice = !isParquet && file.size > maxBytes ? file.slice(0, maxBytes) : file;

    return fileSlice === file
        ? file
        : new File([fileSlice], file.name, { type: file.type });
}
