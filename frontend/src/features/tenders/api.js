import { api } from "../../services/api";

// Fallback sample tenders for offline/demo resilience
const MOCK_TENDERS = [
  {
    id: 1,
    reference_number: "GEM/2026/B/894102",
    title: "Supply & Commissioning of High-Pressure Industrial Valves",
    department: "Chennai Petroleum Corporation Limited (CPCL)",
    category: "Industrial Equipment",
    minimum_turnover: 50000000,
    min_local_content: 50,
    closing_date: "2026-10-15T18:00:00Z",
    status: "ACTIVE",
    created_at: "2026-08-01T10:00:00Z"
  },
  {
    id: 2,
    reference_number: "GEM/2026/B/910344",
    title: "Annual Rate Contract for Refinery Maintenance Services",
    department: "Refinery Engineering Division",
    category: "Services",
    minimum_turnover: 120000000,
    min_local_content: 60,
    closing_date: "2026-09-30T17:00:00Z",
    status: "ACTIVE",
    created_at: "2026-08-10T11:30:00Z"
  },
  {
    id: 3,
    reference_number: "GEM/2026/B/782190",
    title: "Procurement of Heat Exchangers & Pressure Vessels",
    department: "CPCL Mechanical Dept",
    category: "Software & Hardware",
    minimum_turnover: 80000000,
    min_local_content: 50,
    closing_date: "2026-11-05T15:00:00Z",
    status: "ACTIVE",
    created_at: "2026-08-15T09:00:00Z"
  }
];

export const tendersApi = {
  getTenders: async () => {
    try {
      const response = await api.get("/tenders");
      if (response.data && response.data.length > 0) return response.data;
      return MOCK_TENDERS;
    } catch {
      return MOCK_TENDERS;
    }
  },

  getTenderById: async (tenderId) => {
    try {
      const response = await api.get(`/tenders/${tenderId}`);
      return response.data;
    } catch {
      const found = MOCK_TENDERS.find((t) => t.id === Number(tenderId));
      return found || MOCK_TENDERS[0];
    }
  },

  createTender: async (tenderData) => {
    const response = await api.post("/tenders", tenderData);
    return response.data;
  },

  getTenderRequirements: async (tenderId) => {
    try {
      const response = await api.get(`/tenders/${tenderId}/requirements`);
      if (response.data && response.data.length > 0) return response.data;
      return getMockRequirements(tenderId);
    } catch {
      return getMockRequirements(tenderId);
    }
  },

  createTenderRequirement: async (tenderId, requirementData) => {
    const response = await api.post(`/tenders/${tenderId}/requirements`, requirementData);
    return response.data;
  },

  extractTenderRequirements: async (tenderId, extractRequest) => {
    const response = await api.post(`/tenders/${tenderId}/requirements/extract`, extractRequest);
    return response.data;
  },

  getTenderBids: async (tenderId) => {
    try {
      const response = await api.get(`/bid-submissions`);
      const allSubmissions = response.data || [];
      const filtered = allSubmissions.filter(s => s.tender_id === Number(tenderId));
      return filtered.length > 0 ? filtered : getMockSubmissions(tenderId);
    } catch {
      return getMockSubmissions(tenderId);
    }
  },
};

function getMockRequirements(tenderId) {
  return [
    {
      id: 101,
      tender_id: Number(tenderId),
      requirement_code: "UDYAM_MSME_VALID",
      title: "Udyam / MSME Active Registration Certificate",
      description: "Bidder must possess a valid Udyam registration certificate matching company PAN.",
      is_mandatory: true,
      category: "STATUTORY",
      evaluator_name: "UdyamRequirementEvaluator"
    },
    {
      id: 102,
      tender_id: Number(tenderId),
      requirement_code: "GST_ACTIVE_FILING",
      title: "Active GSTIN & GSTR-3B Tax Filing Compliance",
      description: "GSTIN must be ACTIVE with regular monthly return filings and zero default status.",
      is_mandatory: true,
      category: "STATUTORY",
      evaluator_name: "GstRequirementEvaluator"
    },
    {
      id: 103,
      tender_id: Number(tenderId),
      requirement_code: "MII_LOCAL_CONTENT_50",
      title: "Make in India Class-1 / Class-2 Local Content Certificate",
      description: "Minimum 50% local content self-declaration required as per MII CPSE guidelines.",
      is_mandatory: true,
      category: "REGULATORY",
      evaluator_name: "MakeInIndiaRequirementEvaluator"
    },
    {
      id: 104,
      tender_id: Number(tenderId),
      requirement_code: "NON_DEBARRED_CLEARANCE",
      title: "GeM & CPSE Blacklisting / Debarment Clearance",
      description: "Bidder & Directors must not be debarred by Ministry of Petroleum or GeM portal.",
      is_mandatory: true,
      category: "ELIGIBILITY",
      evaluator_name: "DebarmentRequirementEvaluator"
    },
    {
      id: 105,
      tender_id: Number(tenderId),
      requirement_code: "OEM_AUTHORIZATION_LETTER",
      title: "Original Equipment Manufacturer (OEM) Authorization",
      description: "Mandatory OEM authorization letter for key industrial components.",
      is_mandatory: false,
      category: "TECHNICAL",
      evaluator_name: "OemAuthorizationRequirementEvaluator"
    }
  ];
}

function getMockSubmissions(tenderId) {
  return [
    {
      id: 1,
      tender_id: Number(tenderId),
      bidder_id: 10,
      bidder_name: "Apex Engineering Technologies Pvt Ltd",
      gstin: "33AAACA1234A1Z5",
      pan: "AAACA1234A",
      submitted_at: "2026-08-20T14:30:00Z",
      status: "VERIFIED",
      compliance_score: 95.0,
      risk_level: "LOW_RISK"
    },
    {
      id: 2,
      tender_id: Number(tenderId),
      bidder_id: 11,
      bidder_name: "Bharat Valve Solutions & Piping Co",
      gstin: "27BBBCC5678B1Z2",
      pan: "BBBCC5678B",
      submitted_at: "2026-08-22T09:15:00Z",
      status: "FLAGGED",
      compliance_score: 72.5,
      risk_level: "MEDIUM_RISK"
    },
    {
      id: 3,
      tender_id: Number(tenderId),
      bidder_id: 12,
      bidder_name: "Vanguard Heavy Industries (P) Ltd",
      gstin: "07CCCDE9012C1Z8",
      pan: "CCCDE9012C",
      submitted_at: "2026-08-25T16:45:00Z",
      status: "UNDER_REVIEW",
      compliance_score: 40.0,
      risk_level: "HIGH_RISK"
    }
  ];
}

