import { useState } from 'react';
import constitutionData from '../data/constitution_flattened.json';

const constitutionByDocId = new Map(
	constitutionData.map((entry) => [String(entry.doc_id), entry])
);

const getConstitutionEntry = (docId) => {
	if (docId === undefined || docId === null) return null;
	const normalizedDocId = String(docId).trim();
	return constitutionByDocId.get(normalizedDocId) || null;
};

const getRelatedArticleEntry = (entry) => {
	if (!entry || entry.article_no === undefined || entry.article_no === null)
		return null;

	const relatedArticle = constitutionData.find(
		(item) =>
			String(item.level).toLowerCase() === 'article' &&
			item.article_no === entry.article_no &&
			item.part_no === entry.part_no
	);

	if (!relatedArticle) return null;
	if (String(relatedArticle.doc_id) === String(entry.doc_id)) return null;

	return relatedArticle;
};

const ResultDisplay = ({ data, loading, streamedResponse }) => {
	const [openId, setOpenId] = useState(null);

	const displayResponse = streamedResponse || data?.response || '';

	const toggle = (doc_id) =>
		setOpenId((prev) => (prev === doc_id ? null : doc_id));

	return (
		<div className="w-full max-w-6xl mx-auto mt-10 px-6 py-6 bg-gray-100 rounded-2xl space-y-6">
			{data?.query && (
				<div>
					<p className="text-xs uppercase tracking-widest text-gray-500 mb-1">
						Query
					</p>
					<p className="text-lg font-semibold text-gray-900">{data.query}</p>
				</div>
			)}

			{loading && !data?.articles && (
				<div className="flex items-center gap-2 text-gray-400 text-sm">
					<div className="h-4 w-4 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600" />
					Retrieving relevant articles...
				</div>
			)}

			<div className="md:grid md:grid-cols-5 md:gap-10">
				{displayResponse && (
					<div className="md:col-span-3 pl-4 border-l-2 border-blue-300">
						<p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">
							{displayResponse}
							{loading && (
								<span className="inline-block w-1.5 h-4 bg-blue-600 ml-0.5 animate-pulse" />
							)}
						</p>
					</div>
				)}

				{data?.articles?.length > 0 && (
					<div className={`${displayResponse ? 'md:col-span-2' : 'md:col-span-5'} space-y-2 md:max-h-[70vh] md:overflow-y-auto md:pr-2`}>
					<div className="space-y-1.5">
						{data.articles.map((article, index) => {
							const isOpen = openId === article.doc_id;
							const constitutionEntry = getConstitutionEntry(
								article.doc_id
							);
							const displayEntry = constitutionEntry || article;
							const relatedArticle =
								getRelatedArticleEntry(displayEntry);
							return (
								<div key={`${article.doc_id}-${index}`}>
									<button
										onClick={() => toggle(article.doc_id)}
										className="w-full text-left bg-white hover:bg-gray-50 border border-gray-200 flex items-center gap-2.5 transition-colors"
										style={{
											borderRadius: isOpen
												? '8px 8px 0 0'
												: '8px',
											borderColor: isOpen
												? '#3b82f6'
												: '#e5e7eb',
											padding: isOpen
												? '10px 12px'
												: '8px 12px',
										}}
									>
										<span className="text-[11px] text-gray-400 w-4 shrink-0">
											#{index + 1}
										</span>

										<div className="flex-1 min-w-0">
											<p className="text-xs font-semibold text-gray-800 truncate">
												{displayEntry.title}
											</p>
											<p className="text-[11px] text-gray-500 mt-0.5">
												{displayEntry.citation}
											</p>
										</div>

										<svg
											width="16"
											height="16"
											viewBox="0 0 16 16"
											fill="none"
											style={{
												transition: 'transform 0.2s',
												transform: isOpen
													? 'rotate(180deg)'
													: 'rotate(0deg)',
												flexShrink: 0,
											}}
										>
											<path
												d="M4 6l4 4 4-4"
												stroke="#9ca3af"
												strokeWidth="1.5"
												strokeLinecap="round"
												strokeLinejoin="round"
											/>
										</svg>
									</button>

									{isOpen && (
										<div className="bg-blue-50 border border-blue-200 border-t-0 rounded-b-xl px-5 py-4 space-y-2">
											<p className="text-xs text-gray-500">
												Article no:{' '}
												<span className="text-gray-800 font-medium">
													{displayEntry.article_no}
												</span>
											</p>
											<p className="text-xs text-gray-500">
												Clause no:{' '}
												<span className="text-gray-800 font-medium">
													{displayEntry.clause_no ??
														'-'}
												</span>
											</p>
											<p className="text-xs text-gray-500">
												Citation:{' '}
												<span className="text-gray-800 font-medium">
													{displayEntry.citation}
												</span>
											</p>
											<p className="text-xs text-gray-500">
												Doc ID:{' '}
												<span className="text-gray-800 font-medium">
													{article.doc_id}
												</span>
											</p>
											{article.score !== undefined &&
												article.score !== null && (
													<p className="text-xs text-gray-500">
														Score:{' '}
														<span className="text-gray-800 font-medium">
															{Number(
																article.score
															).toFixed(2)}
														</span>
													</p>
												)}
											<p className="text-xs text-gray-500">
												Title:{' '}
												<span className="text-gray-800 font-medium">
													{displayEntry.title}
												</span>
											</p>
											<div className="pt-1">
												<p className="text-xs uppercase tracking-wider text-gray-500 mb-1">
													Provision Text
												</p>
												<p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">
													{displayEntry.text ||
														'No text available.'}
												</p>
											</div>
											{relatedArticle && (
												<div className="pt-1 border-t border-blue-200 mt-2">
													<p className="text-xs uppercase tracking-wider text-gray-500 mb-1">
														Related Article
													</p>
													<p className="text-xs text-gray-500 mb-1">
														Citation:{' '}
														<span className="text-gray-800 font-medium">
															{
																relatedArticle.citation
															}
														</span>
													</p>
													<p className="text-xs text-gray-500 mb-1">
														Title:{' '}
														<span className="text-gray-800 font-medium">
															{
																relatedArticle.title
															}
														</span>
													</p>
													<p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">
														{relatedArticle.text ||
															'No text available.'}
													</p>
												</div>
											)}
										</div>
									)}
								</div>
							);
						})}
					</div>
				</div>
			)}
			</div>
		</div>
	);
};

export default ResultDisplay;
