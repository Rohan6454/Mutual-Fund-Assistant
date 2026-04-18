import Link from "next/link";
import fs from "fs";
import path from "path";

export default function FundsPage() {
  let sources = { sources: [] };
  try {
    const filePath = path.join(process.cwd(), '../data/sources.json');
    const fileContent = fs.readFileSync(filePath, 'utf8');
    sources = JSON.parse(fileContent);
  } catch (e) {
    console.error("Failed to parse sources.json", e);
  }

  const schemes = sources.sources.filter((s: {category: string}) => s.category === "scheme_specific");

  return (
    <div style={{ backgroundColor: '#0a0a0a', color: '#f5f5f5', minHeight: '100vh', fontFamily: 'Inter, sans-serif', paddingBottom: '60px' }}>
      
      {/* Top Navigation */}
      <nav style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '20px 40px', borderBottom: '1px solid #222' }}>
        <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: 'var(--brand-primary)' }}>MF Assistant</div>
        <div style={{ display: 'flex', gap: '30px', fontSize: '0.85rem' }}>
           <Link href="/" style={{ color: '#aaa', textDecoration: 'none' }}>Assistant</Link>
           <Link href="/funds" style={{ color: 'var(--brand-primary)', textDecoration: 'none', borderBottom: '2px solid var(--brand-primary)', paddingBottom: '4px' }}>Funds</Link>
           <Link href="/sources" style={{ color: '#aaa', textDecoration: 'none' }}>Sources</Link>
        </div>
      </nav>

      <main style={{ maxWidth: '1200px', margin: '0 auto', padding: '40px 20px' }}>
         <div style={{ marginBottom: '60px' }}>
            <h1 style={{ fontSize: '3.5rem', fontWeight: 800, margin: 0, lineHeight: 1.1 }}>Scheme <span style={{ color: 'var(--brand-primary)' }}>Library</span></h1>
            <p style={{ color: '#aaa', marginTop: '16px', fontSize: '1.1rem', maxWidth: '600px', lineHeight: 1.5 }}>
               Displaying all schemes currently indexed in the knowledge base. In adherence to our facts-only protocol, synthetic data, unverified metrics, and external fund manager profiles have been removed.
            </p>
         </div>

         <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '24px' }}>
            {schemes.map((scheme: {amc: string, scheme_name: string, notes: string, last_scraped: string, url: string}, idx: number) => (
               <div key={idx} style={{ background: '#111', border: '1px solid #222', borderRadius: '12px', padding: '30px', display: 'flex', flexDirection: 'column', transition: 'transform 0.2s, border-color 0.2s' }}>
                  <div style={{ display: 'inline-block', alignSelf: 'flex-start', padding: '6px 10px', background: 'rgba(234, 179, 8, 0.1)', color: 'var(--brand-primary)', fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '20px', borderRadius: '4px', border: '1px solid rgba(234, 179, 8, 0.2)', fontWeight: 'bold' }}>
                     {scheme.amc}
                  </div>
                  <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', margin: '0 0 16px 0', lineHeight: 1.3 }}>{scheme.scheme_name}</h2>
                  <p style={{ color: '#888', fontSize: '0.9rem', lineHeight: 1.6, flex: 1, marginBottom: '32px' }}>
                     {scheme.notes}
                  </p>
                  
                  <div style={{ borderTop: '1px solid #222', paddingTop: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                     <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#666', fontSize: '0.75rem' }}>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                        Last Indexed: {new Date(scheme.last_scraped).toLocaleDateString()}
                     </div>
                     <a href={scheme.url} target="_blank" rel="noreferrer" style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 12px', background: 'var(--brand-primary)', color: '#000', textDecoration: 'none', borderRadius: '6px', fontSize: '0.75rem', fontWeight: 'bold' }}>
                        Source URL
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                     </a>
                  </div>
               </div>
            ))}
            
            {schemes.length === 0 && (
               <div style={{ gridColumn: '1 / -1', padding: '60px 40px', textAlign: 'center', background: '#111', borderRadius: '12px', border: '1px solid #222' }}>
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#444" strokeWidth="1" style={{ marginBottom: '16px' }}><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                  <h3 style={{ fontSize: '1.25rem', marginBottom: '8px', margin: 0 }}>No Schemes Found</h3>
                  <p style={{ color: '#888', margin: 0 }}>There are currently no scheme-specific sources indexed in your data directory.</p>
               </div>
            )}
         </div>
      </main>
    </div>
  );
}
