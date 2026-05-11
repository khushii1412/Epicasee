# Data Sources

## Overview

This document catalogs all data sources used in the India Multi-Disease Epidemiology Framework. Each data source is documented with its origin, format, update frequency, and any access requirements.

---

## COVID-19

### Primary Sources

| Source | URL | Format | Frequency |
|--------|-----|--------|-----------|
| covid19india.org | https://api.covid19india.org | JSON API | Historical |
| MoHFW Dashboard | https://www.mohfw.gov.in | HTML/PDF | Daily |
| JHU CSSE | https://github.com/CSSEGISandData/COVID-19 | CSV | Daily |

### Data Fields Available

- Date
- State/UT
- District (partial)
- Confirmed cases
- Recovered
- Deceased
- Active cases
- Testing data (partial)

### Notes

- covid19india.org API was retired in late 2021
- Historical data archived locally
- MoHFW data requires web scraping

---

## Dengue

### Primary Sources

| Source | URL | Format | Frequency |
|--------|-----|--------|-----------|
| NVBDCP | https://nvbdcp.gov.in | PDF Reports | Monthly |
| State Health Portals | Various | HTML/PDF | Varies |

### Data Fields Available

- Year/Month
- State
- Suspected cases
- Confirmed cases
- Deaths

### Notes

- Data often released with significant delay
- District-level data inconsistently available
- Requires PDF extraction for many reports

---

## Malaria

### Primary Sources

| Source | URL | Format | Frequency |
|--------|-----|--------|-----------|
| NVBDCP (NVL) | https://nvbdcp.gov.in/malaria-new.html | PDF/XLS | Monthly |
| National Vector Borne Disease Control Programme | Various | Reports | Annual |

### Data Fields Available

- Year/Month
- State
- Total cases (Pf + Pv)
- P. falciparum cases
- P. vivax cases
- Deaths

### Notes

- Malaria data generally more structured
- Annual reports provide comprehensive state-wise data
- PDFs require extraction using tabula/camelot

---

## IDSP (Integrated Disease Surveillance Programme)

### Primary Sources

| Source | URL | Format | Frequency |
|--------|-----|--------|-----------|
| IDSP-NCDC | https://idsp.nic.in | PDF Reports | Weekly |

### Data Fields Available

- Week number
- State
- District
- Disease outbreaks
- Cases
- Deaths

### Notes

- Weekly reports cover all notifiable diseases
- Covers outbreaks, not routine surveillance
- PDF format requires extraction

---

## Data Quality Considerations

### Common Issues

1. **Inconsistent naming**: State/district names vary across sources
2. **Missing data**: Not all states report consistently
3. **Lag**: Data often published weeks or months after collection
4. **Format changes**: Source formats change without notice

### Mitigation Strategies

1. Maintain state/district name mapping tables
2. Implement data validation pipelines
3. Track data provenance and timestamps
4. Version raw data files

---

## Access & Credentials

Most sources are publicly available. Document any required:

- [ ] API keys
- [ ] Login credentials
- [ ] Rate limits
- [ ] Terms of use compliance

---

## Future Sources

| Source | Disease | Priority |
|--------|---------|----------|
| Chikungunya (NVBDCP) | Chikungunya | Medium |
| JE/AES (NVBDCP) | Japanese Encephalitis | Medium |
| TB India | Tuberculosis | High |
| NACO | HIV/AIDS | Low |
