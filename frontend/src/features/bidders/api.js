import { api } from "../../services/api";

const MOCK_BIDDERS = [
  {
    id: 10,
    legal_name: "Apex Engineering Technologies Pvt Ltd",
    gstin: "33AAACA1234A1Z5",
    pan: "AAACA1234A",
    udyam_number: "UDYAM-TN-02-0012345",
    business_type: "Private Limited",
    msme_category: "SMALL",
    contact_email: "contact@apexeng.co.in",
    contact_phone: "+91 98765 43210",
    city: "Chennai",
    state: "Tamil Nadu",
    is_blacklisted: false,
    created_at: "2026-07-15T10:00:00Z"
  },
  {
    id: 11,
    legal_name: "Bharat Valve Solutions & Piping Co",
    gstin: "27BBBCC5678B1Z2",
    pan: "BBBCC5678B",
    udyam_number: "UDYAM-MH-01-0098765",
    business_type: "Partnership Firm",
    msme_category: "MEDIUM",
    contact_email: "info@bharatvalve.com",
    contact_phone: "+91 98123 45678",
    city: "Mumbai",
    state: "Maharashtra",
    is_blacklisted: false,
    created_at: "2026-07-20T11:00:00Z"
  },
  {
    id: 12,
    legal_name: "Vanguard Heavy Industries (P) Ltd",
    gstin: "07CCCDE9012C1Z8",
    pan: "CCCDE9012C",
    udyam_number: "UDYAM-DL-03-0054321",
    business_type: "Private Limited",
    msme_category: "MICRO",
    contact_email: "bids@vanguardheavy.org",
    contact_phone: "+91 99887 76655",
    city: "New Delhi",
    state: "Delhi",
    is_blacklisted: true,
    created_at: "2026-07-25T15:30:00Z"
  }
];

export const biddersApi = {
  getBidders: async () => {
    try {
      const response = await api.get("/bidders");
      if (response.data && response.data.length > 0) return response.data;
      return MOCK_BIDDERS;
    } catch {
      return MOCK_BIDDERS;
    }
  },

  getBidderById: async (bidderId) => {
    try {
      const response = await api.get(`/bidders/${bidderId}`);
      return response.data;
    } catch {
      return MOCK_BIDDERS.find(b => b.id === Number(bidderId)) || MOCK_BIDDERS[0];
    }
  },

  getBidSubmission: async (bidSubmissionId) => {
    try {
      const response = await api.get(`/bid-submissions/${bidSubmissionId}`);
      return response.data;
    } catch {
      return {
        id: Number(bidSubmissionId),
        tender_id: 1,
        bidder_id: 10,
        bidder: MOCK_BIDDERS[0],
        submitted_at: "2026-08-20T14:30:00Z",
        status: "VERIFIED",
        compliance_score: 95.0,
        risk_level: "LOW_RISK"
      };
    }
  },
};

