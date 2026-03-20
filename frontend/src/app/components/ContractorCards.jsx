export default function ContractorCards({ contractors }) {
    if (!contractors?.length) return null;

    return (
        <div className="contractor-cards-row">
            {contractors.map((c, i) => {
                const href = c.maps_url || c.website;
                const Card = href ? 'a' : 'div';
                const linkProps = href
                    ? { href, target: '_blank', rel: 'noopener noreferrer' }
                    : {};

                return (
                    <Card key={i} className={`contractor-card${href ? ' contractor-card-clickable' : ''}`} {...linkProps}>
                        <div className="contractor-card-name">{c.name}</div>
                        <div className="contractor-card-meta">
                            {c.rating != null && (
                                <span>&#9733; {c.rating}{c.review_count != null ? ` (${c.review_count} reviews)` : ''}</span>
                            )}
                            {c.phone && <span>{c.phone}</span>}
                        </div>
                        {c.address && <div className="contractor-card-address">{c.address}</div>}
                        {c.trade && <span className="contractor-card-trade">{c.trade}</span>}
                    </Card>
                );
            })}
        </div>
    );
}
