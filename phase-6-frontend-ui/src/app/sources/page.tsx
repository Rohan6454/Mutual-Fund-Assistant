import Link from "next/link";
import fs from "fs";
import path from "path";

export default function SourcesPage() {
  let sourcesList: {amc?: string, scheme_name?: string, category: string, notes: string, last_scraped: string, url: string, document_format: string, id: string}[] = [];
  try {
    const filePath = path.join(process.cwd(), '../data/sources.json');
    const fileContent = fs.readFileSync(filePath, 'utf8');
    const sourcesData = JSON.parse(fileContent);
    sourcesList = sourcesData.sources || [];
  } catch (e) {
    console.error("Failed to parse sources.json", e);
  }

  return (
    <div className="layout-container animate-fade-in" style={{ backgroundColor: '#0a0a0a', color: '#f5f5f5', display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      
      {/* Top Header */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '20px 40px', borderBottom: '1px solid #1a1a1a', zIndex: 10 }}>
         <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ fontStyle: 'italic', fontWeight: 800, fontSize: '1.25rem' }}>MF <span style={{ color: 'var(--brand-primary)' }}>Assistant</span></div>
         </div>
         <div style={{ display: 'flex', gap: '32px', fontSize: '0.85rem' }}>
            <Link href="/" style={{ color: '#aaa', textDecoration: 'none' }}>Assistant</Link>
            <Link href="/funds" style={{ color: '#aaa', textDecoration: 'none' }}>Funds</Link>
            <Link href="/sources" style={{ color: 'var(--brand-primary)', textDecoration: 'none', borderBottom: '2px solid var(--brand-primary)', paddingBottom: '4px' }}>Sources</Link>
         </div>
      </header>

      <div style={{ display: 'flex', flex: 1 }}>
         {/* Main Content Pane */}
         <main style={{ flex: 1, padding: '60px', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '40px', maxWidth: '1000px', margin: '0 auto 40px auto' }}>
               <div>
                 <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                    <div style={{ background: 'var(--brand-primary)', color: '#000', fontSize: '0.65rem', fontWeight: 'bold', padding: '4px 8px', borderRadius: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"></polyline></svg> OFFICIAL KNOWLEDGE BASE
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#888' }}>{sourcesList.length} Authenticated Sources Map</div>
                 </div>
                 <h1 style={{ fontSize: '3.5rem', fontWeight: 800, margin: 0, letterSpacing: '-1px' }}>Source <span style={{ color: 'var(--brand-primary)' }}>Library</span></h1>
                 <p style={{ color: '#aaa', fontSize: '1.1rem', marginTop: '16px', maxWidth: '600px', lineHeight: 1.5 }}>
                   Access the foundational logic of the Assistant. Every fact, statistic, or guideline produced is strictly scoped to the documents cataloged below.
                 </p>
               </div>
            </div>

            <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
               {/* Verified Document Manifest */}
               <div style={{ background: '#111', borderRadius: '12px', border: '1px solid #222', padding: '12px 24px' }}>
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                     
                     <div style={{ display: 'flex', padding: '16px', borderBottom: '1px solid #222', color: '#666', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '1px', fontWeight: 'bold' }}>
                        <div style={{ flex: 2 }}>Document Outline</div>
                        <div style={{ flex: 1 }}>Category</div>
                        <div style={{ flex: 1, textAlign: 'right' }}>Format</div>
                        <div style={{ width: '40px' }}></div>
                     </div>

                     {sourcesList.map((source: {amc?: string, scheme_name?: string, category: string, notes: string, last_scraped: string, url: string, document_format: string, id: string}, idx: number) => (
                        <div key={idx} style={{ display: 'flex', alignItems: 'center', padding: '20px 16px', borderBottom: idx === sourcesList.length - 1 ? 'none' : '1px solid #1a1a1a' }}>
                           <div style={{ flex: 2, paddingRight: '20px' }}>
                              <h4 style={{ fontSize: '1rem', margin: '0 0 8px 0', color: '#eee' }}>{source.notes || source.scheme_name || source.id}</h4>
                              <div style={{ display: 'flex', gap: '12px', fontSize: '0.75rem', color: '#666', alignItems: 'center' }}>
                                <span>ID: {source.id}</span> • <span>Entity: {source.amc || source.scheme_name || "General"}</span>
                              </div>
                           </div>
                           <div style={{ flex: 1, color: '#aaa', fontSize: '0.85rem' }}>
                              <span style={{ padding: '4px 8px', background: '#1a1a1a', borderRadius: '4px', border: '1px solid #333' }}>
                                 {source.category}
                              </span>
                           </div>
                           <div style={{ flex: 1, textAlign: 'right', display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '8px', color: '#888', fontSize: '0.85rem' }}>
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                              {source.document_format.toUpperCase()}
                           </div>
                           <div style={{ width: '40px', textAlign: 'right' }}>
                              <a href={source.url} target="_blank" rel="noreferrer" style={{ color: 'var(--brand-primary)', textDecoration: 'none', display: 'inline-flex', padding: '8px', borderRadius: '4px', background: 'rgba(234, 179, 8, 0.1)', transition: 'background 0.2s' }} title="Visit Original URL">
                                 <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                              </a>
                           </div>
                        </div>
                     ))}

                     {sourcesList.length === 0 && (
                        <div style={{ padding: '40px', textAlign: 'center', color: '#888' }}>
                           No sources indexed in database.
                        </div>
                     )}

                  </div>
               </div>
            </div>
         </main>
      </div>
    </div>
  );
}
