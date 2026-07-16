import toast from 'react-hot-toast';
import { API_BASE_URL } from '../config/environment';

export async function loadStaticWikidataSeriesDetail(qid) {
  const token = localStorage.getItem('token');
  const r = await fetch(
    `${API_BASE_URL}/api/static-wikidata/series/${encodeURIComponent(qid)}`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  if (!r.ok) throw new Error('fetch');
  return r.json();
}

export function buildSeriesStateFromStaticDetail(item, detail) {
  return {
    ...item,
    name: detail.name_fr || detail.name || detail.name_en || item.name,
    author: item.author || '',
    fromStaticWikidata: true,
    staticWikidataDetail: detail,
    totalBooks: detail.work_count ?? (detail.works || []).length,
    wikidata_qid: detail.qid || item.wikidata_qid,
  };
}

export async function openStaticWikidataSeriesModal(item, setSelectedSeries, setShowSeriesModal) {
  if (!item?.wikidata_qid) return;
  try {
    const detail = await loadStaticWikidataSeriesDetail(item.wikidata_qid);
    setSelectedSeries(buildSeriesStateFromStaticDetail(item, detail));
    setShowSeriesModal(true);
  } catch {
    toast.error('Impossible de charger la série Wikidata');
  }
}
