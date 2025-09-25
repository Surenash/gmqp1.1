import React, { useState, useEffect, useRef } from 'react';
import ReactDOM from 'react-dom/client';

// --- API Client ---
const API_BASE_URL = '/api'; // Using relative URL for proxying

const getTokens = () => ({
    access: localStorage.getItem('accessToken'),
    refresh: localStorage.getItem('refreshToken'),
});

const setTokens = (access: string, refresh: string) => {
    localStorage.setItem('accessToken', access);
    localStorage.setItem('refreshToken', refresh);
};

const clearTokens = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
};

// --- Constants for Manufacturer Signup & Directory ---
const PRODUCTION_VOLUMES = ['Prototyping', 'Low Volume', 'Medium Volume', 'High Volume'];
const CERTIFICATIONS = ['ISO 9001', 'AS9100', 'IATF 16949', 'ISO 13485 (Medical)', 'RoHS Compliant'];
const MACHINING_PROCESSES = ['CNC Milling (3-axis)', 'CNC Milling (4-axis)', 'CNC Milling (5-axis)', 'CNC Turning', 'Swiss Machining', 'EDM (Electrical Discharge Machining)', 'Grinding / Lapping'];
const SHEET_METAL_PROCESSES = ['Laser Cutting', 'Waterjet Cutting', 'Plasma Cutting', 'Bending (Press Brake)', 'Punching', 'Sheet Metal Welding'];
const CASTING_PROCESSES = ['Sand Casting', 'Die Casting', 'Investment Casting', 'Gravity Casting'];
const FORGING_PROCESSES = ['Open Die Forging', 'Closed Die Forging', 'Cold Forging'];
const INJECTION_MOLDING_PROCESSES = ['Thermoplastics', 'Thermosets', 'Insert Molding / Overmolding'];
const ADDITIVE_PROCESSES = ['FDM', 'SLA', 'SLS', 'DMLS / SLM (Metal)', 'Multi Jet Fusion (MJF)'];
const WELDING_JOINING_PROCESSES = ['MIG Welding', 'TIG Welding', 'Spot Welding', 'Laser Welding', 'Brazing / Soldering', 'Riveting / Adhesives'];
const MATERIALS_METALS = ['Aluminum', 'Steel (Mild, Stainless, Tool)', 'Titanium', 'Brass', 'Copper'];
const MATERIALS_PLASTICS = ['ABS', 'Nylon', 'POM', 'Polycarbonate', 'PEEK', 'PE', 'PP', 'Acrylic (PMMA)'];
const MATERIALS_COMPOSITES = ['CFRP (Carbon Fiber)', 'GFRP (Glass Fiber)'];
const MATERIALS_OTHERS = ['Rubber', 'Silicone', 'Foam', 'Ceramics'];
const SURFACE_FINISHES = ['Sandblasting', 'Anodizing (Type I, II, III)', 'Powder Coating', 'Electroplating (Chrome, Nickel, Zinc)', 'Polishing', 'Heat Treatment'];
const POST_PROCESSING_ASSEMBLY = ['Threading / Tapping', 'Press-fitting', 'Assembly Welding', 'Fastening', 'Full Product Assembly', 'Custom Packaging'];
const FILE_FORMATS = ['STEP (.stp, .step)', 'IGES (.igs, .iges)', 'SolidWorks (.sldprt)', 'PDF (Drawings)', 'DXF'];
const INCOTERMS = ['EXW (Ex Works)', 'FOB (Free On Board)', 'DDP (Delivered Duty Paid)'];
const SPECIAL_CAPABILITIES = ['Clean Room Manufacturing', 'Aerospace Grade', 'Medical Grade', 'Supply Chain Integration', 'Custom Tooling / Mold Making', 'Rapid Prototyping', 'Lights-Out Manufacturing'];
const ORDER_STATUSES = ['Awaiting Production', 'In Production', 'Shipped', 'Delivered', 'Cancelled'];

const ALL_CAPABILITIES_GROUPS = [
    { title: 'Machining', processes: MACHINING_PROCESSES },
    { title: 'Sheet Metal', processes: SHEET_METAL_PROCESSES },
    { title: 'Casting', processes: CASTING_PROCESSES },
    { title: 'Forging', processes: FORGING_PROCESSES },
    { title: 'Injection Molding', processes: INJECTION_MOLDING_PROCESSES },
    { title: '3D Printing', processes: ADDITIVE_PROCESSES },
    { title: 'Welding & Joining', processes: WELDING_JOINING_PROCESSES },
];

const ALL_CAPABILITIES_FLAT = ALL_CAPABILITIES_GROUPS.flatMap(g => g.processes);

const mockManufacturers = [
    { id: '1', company_name: 'Precision Parts Co.', location: 'Munich, Germany', rating: 4.9, logoUrl: `https://avatar.vercel.sh/precision.svg?text=PP`, capabilities: [MACHINING_PROCESSES[0], MACHINING_PROCESSES[2], SHEET_METAL_PROCESSES[0], MATERIALS_METALS[0], MATERIALS_METALS[1]], certifications: [CERTIFICATIONS[0], CERTIFICATIONS[1]] },
    { id: '2', company_name: 'Rapid Proto Labs', location: 'Austin, TX, USA', rating: 4.7, logoUrl: `https://avatar.vercel.sh/rapid.svg?text=RL`, capabilities: [ADDITIVE_PROCESSES[0], ADDITIVE_PROCESSES[1], ADDITIVE_PROCESSES[4], MATERIALS_PLASTICS[0], MATERIALS_PLASTICS[1]], certifications: [CERTIFICATIONS[0]] },
    { id: '3', company_name: 'Global Moldings Inc.', location: 'Shenzhen, China', rating: 4.8, logoUrl: `https://avatar.vercel.sh/global.svg?text=GM`, capabilities: [INJECTION_MOLDING_PROCESSES[0], INJECTION_MOLDING_PROCESSES[2], MATERIALS_PLASTICS[2], MATERIALS_PLASTICS[3]], certifications: [CERTIFICATIONS[2]] },
    { id: '4', company_name: 'AeroWeld Experts', location: 'Toulouse, France', rating: 5.0, logoUrl: `https://avatar.vercel.sh/aero.svg?text=AE`, capabilities: [WELDING_JOINING_PROCESSES[1], WELDING_JOINING_PROCESSES[3], MATERIALS_METALS[2]], certifications: [CERTIFICATIONS[1], CERTIFICATIONS[4]] },
    { id: '5', company_name: 'Midwest Metalworks', location: 'Chicago, IL, USA', rating: 4.6, logoUrl: `https://avatar.vercel.sh/midwest.svg?text=MM`, capabilities: [SHEET_METAL_PROCESSES[1], SHEET_METAL_PROCESSES[3], CASTING_PROCESSES[0], MATERIALS_METALS[1]], certifications: [] },
    { id: '6', company_name: 'Titanium Forge', location: 'Sheffield, UK', rating: 4.9, logoUrl: `https://avatar.vercel.sh/titanium.svg?text=TF`, capabilities: [FORGING_PROCESSES[1], MACHINING_PROCESSES[3], MATERIALS_METALS[2]], certifications: [CERTIFICATIONS[0]] },
    { id: '7', company_name: 'MedTech Devices', location: 'Zurich, Switzerland', rating: 5.0, logoUrl: `https://avatar.vercel.sh/medtech.svg?text=MD`, capabilities: [MACHINING_PROCESSES[4], ADDITIVE_PROCESSES[3], POST_PROCESSING_ASSEMBLY[0], MATERIALS_PLASTICS[4], MATERIALS_METALS[2]], certifications: [CERTIFICATIONS[3], CERTIFICATIONS[0]] },
    { id: '8', company_name: 'Dynamic Die-Casting', location: 'Nagoya, Japan', rating: 4.7, logoUrl: `https://avatar.vercel.sh/dynamic.svg?text=DD`, capabilities: [CASTING_PROCESSES[1], CASTING_PROCESSES[2], MATERIALS_METALS[0]], certifications: [CERTIFICATIONS[2]] },
];

// --- Mock Data for Dashboards ---
const mockManufacturerProfile = {
    companyName: 'Precision Parts Co.', email: 'contact@precisionparts.com', location: 'Munich, Germany', website: 'https://precisionparts.com', productionVolume: 'Medium Volume', leadTimeRange: '7-14 business days', moq: '25', certifications: [CERTIFICATIONS[0], CERTIFICATIONS[1]], otherCertifications: 'Custom Aerospace Cert', qualityControlProcesses: 'First Article Inspection (FAI), In-process quality checks with CMM, Final inspection reports provided with every order.', materialTesting: 'XRF Analyzer for material verification, Hardness testing equipment.', machining: [MACHINING_PROCESSES[0], MACHINING_PROCESSES[2]], sheetMetal: [SHEET_METAL_PROCESSES[0]], casting: [], forging: [], injectionMolding: { processes: [], cavityCount: '', moldClass: '' }, '3dPrinting': [], weldingJoining: [], supportedMaterials: [MATERIALS_METALS[0], MATERIALS_METALS[1]],
    logoUrl: `https://avatar.vercel.sh/precision.svg?text=PP`,
    backgroundUrl: `https://picsum.photos/seed/bg1/1600/400`,
    portfolio: [
        { id: 1, type: 'image', title: 'Aerospace Bracket', url: `https://picsum.photos/seed/mfg1/400/300` },
        { id: 2, type: 'image', title: 'Medical Device Housing', url: `https://picsum.photos/seed/mfg2/400/300` },
        { id: 3, type: 'image', title: 'Automotive Gear Component', url: `https://picsum.photos/seed/mfg3/400/300` },
    ],
};
let mockCustomerDesignsData = [
    { id: 'D-101', name: 'Main Housing V2', material: 'Aluminum', quantity: 50, status: 'Quoting', dateUploaded: '2024-07-28T10:00:00Z', files: { primary: { name: 'main_housing_v2.step', size: '2.3 MB' }, supporting: [{ name: 'drawing.pdf', size: '500 KB' }] } }, 
    { id: 'D-102', name: 'Actuator Mounting Bracket', material: 'Titanium', quantity: 10, status: 'Quoting', dateUploaded: '2024-07-27T15:30:00Z', files: { primary: { name: 'actuator_mount_bracket_rev4.iges', size: '850 KB' }, supporting: [] } },
    { id: 'D-103', name: 'Enclosure Lid', material: 'ABS', quantity: 200, status: 'Ordered', dateUploaded: '2024-07-27T09:00:00Z', files: { primary: { name: 'enclosure_lid_final.stl', size: '5.1 MB' }, supporting: [{ name: 'assembly_instructions.pdf', size: '1.2 MB' }, { name: 'tolerance_spec.dxf', size: '250 KB' }] } }, 
    { id: 'D-104', name: 'Custom Heatsink', material: 'Copper', quantity: 25, status: 'Quoting', dateUploaded: '2024-07-26T12:00:00Z', files: { primary: { name: 'heatsink_v3.step', size: '1.1 MB' }, supporting: [] } },
    { id: 'D-105', name: 'Gearbox Casing', material: 'Steel (Stainless)', quantity: 30, status: 'Analysis Complete', dateUploaded: '2024-07-25T18:00:00Z', files: { primary: { name: 'gearbox_casing.sldprt', size: '4.8 MB' }, supporting: [] } },
    { id: 'D-106', name: 'Robotic Arm Joint', material: 'Aluminum', quantity: 15, status: 'Ordered', dateUploaded: '2024-07-29T09:00:00Z', files: { primary: { name: 'robot_joint_assy.step', size: '3.4 MB' }, supporting: [] } },
    { id: 'D-107', name: 'Mounting Plate', material: 'Steel (Mild)', quantity: 30, status: 'Ordered', dateUploaded: '2024-07-22T14:00:00Z', files: { primary: { name: 'plate.dxf', size: '150 KB' }, supporting: [] } },
    { id: 'D-108', name: 'Display Bezel', material: 'Polycarbonate', quantity: 150, status: 'Ordered', dateUploaded: '2024-07-15T10:00:00Z', files: { primary: { name: 'bezel_inj_mold.step', size: '2.9 MB' }, supporting: [] } },
    { id: 'D-109', name: 'Sensor Mount', material: 'Nylon', quantity: 150, status: 'Analysis Failed', dateUploaded: '2024-07-24T11:00:00Z', files: { primary: { name: 'sensor_mount.stl', size: '750 KB' }, supporting: [{name: 'error_log.txt', size: '5 KB'}] } },
];
const mockQuoteRequests = [
    { id: 'QR-001', designId: 'D-101', designName: 'Main Housing V2', customer: 'Innovate Robotics', material: 'Aluminum', quantity: 50, surfaceFinish: 'Anodizing (Type II)', dateReceived: '2024-07-28T10:00:00Z', status: 'Pending' }, { id: 'QR-002', designId: 'D-102', designName: 'Actuator Mounting Bracket', customer: 'AeroInnovate', material: 'Titanium', quantity: 10, surfaceFinish: 'None', dateReceived: '2024-07-27T15:30:00Z', status: 'Pending' }, { id: 'QR-003', designId: 'D-103', designName: 'Enclosure Lid', customer: 'BioMechanics Inc.', material: 'ABS', quantity: 200, surfaceFinish: 'Polishing', dateReceived: '2024-07-27T09:00:00Z', status: 'Quoted' }, { id: 'QR-004', designId: 'D-104', designName: 'Custom Heatsink', customer: 'Quantum Drive', material: 'Copper', quantity: '25', surfaceFinish: 'Electroplating (Nickel)', dateReceived: '2024-07-26T12:00:00Z', status: 'Declined' }, { id: 'QR-005', designId: 'D-105', designName: 'Gearbox Casing', customer: 'Innovate Robotics', material: 'Steel (Stainless)', quantity: 30, surfaceFinish: 'Sandblasting', dateReceived: '2024-07-25T18:00:00Z', status: 'Pending' },
];
const mockActiveOrders = [
    { id: 'ORD-001', designId: 'D-103', designName: 'Enclosure Lid', customer: 'BioMechanics Inc.', quotePrice: 1850.00, quantity: 200, status: 'In Production', dateCreated: '2024-07-28T11:00:00Z', trackingNumber: null, shippingCarrier: null }, { id: 'ORD-002', designId: 'D-106', designName: 'Robotic Arm Joint', customer: 'Innovate Robotics', quotePrice: 3200.00, quantity: 15, status: 'Awaiting Production', dateCreated: '2024-07-29T09:00:00Z', trackingNumber: null, shippingCarrier: null }, { id: 'ORD-003', designId: 'D-107', designName: 'Mounting Plate', customer: 'AeroInnovate', quotePrice: 750.00, quantity: 30, status: 'Shipped', dateCreated: '2024-07-22T14:00:00Z', trackingNumber: '1Z9999W99999999999', shippingCarrier: 'UPS' }, { id: 'ORD-004', designId: 'D-108', designName: 'Display Bezel', customer: 'Quantum Drive', quotePrice: 450.00, quantity: 150, status: 'Delivered', dateCreated: '2024-07-15T10:00:00Z', trackingNumber: '9405500000000000000000', shippingCarrier: 'USPS' }
];
const mockCustomerProfileData = { companyName: 'Innovate Robotics', email: 'contact@innovate-robotics.com' };
const mockCustomerOrdersData = [
    { id: 'ORD-001', designId: 'D-103', designName: 'Enclosure Lid', manufacturer: 'Global Moldings Inc.', price: 1850.00, status: 'In Production', orderDate: '2024-07-28T11:00:00Z', trackingNumber: null, shippingCarrier: null }, { id: 'ORD-003', designId: 'D-107', designName: 'Mounting Plate', manufacturer: 'AeroWeld Experts', price: 750.00, status: 'Shipped', orderDate: '2024-07-22T14:00:00Z', trackingNumber: '1Z9999W99999999999', shippingCarrier: 'UPS' }, { id: 'ORD-004', designId: 'D-108', designName: 'Display Bezel', manufacturer: 'Rapid Proto Labs', price: 450.00, status: 'Delivered', orderDate: '2024-07-15T10:00:00Z', trackingNumber: '9405500000000000000000', shippingCarrier: 'USPS' }
];


const api = {
    async request(endpoint: string, options: RequestInit = {}) {
        const headers = new Headers(options.headers || {});
        const { access } = getTokens();
        if (access) {
            headers.set('Authorization', `Bearer ${access}`);
        }
        if (options.body && !(options.body instanceof FormData)) {
            headers.set('Content-Type', 'application/json');
            options.body = JSON.stringify(options.body);
        }

        const response = await fetch(`${API_BASE_URL}${endpoint}`, { ...options, headers });

        if (!response.ok) {
            if (response.status === 401) {
                clearTokens();
                window.location.href = '/login';
            }
            const errorData = await response.json().catch(() => ({ detail: 'An unexpected error occurred.' }));
            throw new Error(errorData.detail || `Request failed with status ${response.status}`);
        }

        if (response.status === 204) { return null; }
        return response.json();
    },

    login(credentials: object) {
        return this.request('/auth/token/', { method: 'POST', body: JSON.stringify(credentials) });
    },
    
    register(userData: object) {
        return this.request('/auth/register/', { method: 'POST', body: JSON.stringify(userData) });
    },

    getMe() {
        return this.request('/auth/me/');
    },

    getDesigns() {
        return this.request('/designs/');
    },

    deleteDesign(id: string) {
        return this.request(`/designs/${id}/`, { method: 'DELETE' });
    },

    getUploadUrl(fileName: string, fileType: string) {
        return this.request('/designs/upload-url/', { method: 'POST', body: JSON.stringify({ fileName, fileType }) });
    },

    async uploadFileToS3(url: string, file: File) {
        const response = await fetch(url, {
            method: 'PUT',
            body: file,
            headers: { 'Content-Type': file.type }
        });
        if (!response.ok) { throw new Error('Failed to upload file to S3.'); }
    },

    createDesign(designData: object) {
        return this.request('/designs/', { method: 'POST', body: JSON.stringify(designData) });
    },
    
    updateManufacturerProfile(profileData: object) {
        console.log("MOCK API: Updating manufacturer profile with:", profileData);
        // In a real app, this would handle file uploads to S3 and return URLs
        Object.assign(mockManufacturerProfile, profileData);
        return new Promise(resolve => setTimeout(() => resolve({ success: true, updatedData: profileData }), 500));
    },
    
    // MOCK APIs for Manufacturer Dashboard
    getManufacturerProfile(): Promise<any> {
        console.log("MOCK API: Fetching manufacturer profile...");
        return new Promise(resolve => setTimeout(() => resolve(mockManufacturerProfile), 500));
    },

    getQuoteRequests() {
        console.log("MOCK API: Fetching quote requests...");
        return new Promise(resolve => setTimeout(() => resolve(mockQuoteRequests), 700));
    },

    submitQuote(designId: string, quoteData: object) {
        console.log(`MOCK API: Submitting quote for design ${designId}:`, quoteData);
        return new Promise(resolve => setTimeout(() => resolve({ success: true, designId, quoteData }), 500));
    },

    declineQuoteRequest(designId: string) {
        console.log(`MOCK API: Declining quote request for design ${designId}`);
        return new Promise(resolve => setTimeout(() => resolve({ success: true, designId }), 300));
    },

    getActiveOrders() {
        console.log("MOCK API: Fetching active orders...");
        return new Promise(resolve => setTimeout(() => resolve(mockActiveOrders), 600));
    },
    
    updateOrder(orderId: string, orderData: object) {
        console.log(`MOCK API: Updating order ${orderId} with:`, orderData);
        const orderIndex = mockActiveOrders.findIndex(o => o.id === orderId);
        if (orderIndex !== -1) {
            mockActiveOrders[orderIndex] = { ...mockActiveOrders[orderIndex], ...orderData };
        }
        return new Promise(resolve => setTimeout(() => resolve({ success: true, orderId, updatedData: orderData }), 500));
    },

    // MOCK API for Manufacturer Directory
    getManufacturers(): Promise<unknown> {
        console.log("Fetching mock manufacturers...");
        return new Promise(resolve => setTimeout(() => resolve(mockManufacturers), 500));
    },

    getManufacturerById(id): Promise<any> {
        console.log(`Fetching mock manufacturer with id: ${id}`);
        const manufacturer = mockManufacturers.find(m => m.id === id);

        return new Promise(resolve => setTimeout(() => {
            if (manufacturer) {
                const detailedData = {
                    ...manufacturer,
                    ...mockManufacturerProfile, // Use shared profile for details
                    company_name: manufacturer.company_name, // ensure correct name
                    location: manufacturer.location,
                    rating: manufacturer.rating,
                    logoUrl: manufacturer.logoUrl,
                    about: `Founded in 2005, ${manufacturer.company_name} has grown to become a leader in precision manufacturing. We specialize in complex parts for the aerospace, medical, and automotive industries. Our commitment to quality, innovation, and on-time delivery is unwavering. We leverage state-of-the-art technology and a highly skilled team to tackle the most demanding projects.`,
                    equipment: ['Haas VF-4 (5-axis)', 'Okuma GENOS L300-M', 'Keyence IM-8000', 'Zeiss CMM', 'Markforged Metal X', 'HP Multi Jet Fusion 5200'],
                    reviews: [
                        { id: 1, author: 'Jane D., AeroInnovate', rating: 5, comment: 'Excellent quality and communication. Delivered ahead of schedule, which was critical for our project timeline.' },
                        { id: 2, author: 'John S., BioMechanics Inc.', rating: 4, comment: 'Good parts, but one was slightly out of tolerance. They were very responsive and shipped a replacement part overnight.' },
                        { id: 3, author: 'Emily R., Quantum Drive', rating: 5, comment: 'The team at Precision Parts is top-notch. Their engineering feedback during the quoting phase was invaluable and saved us from a costly design flaw.' },
                    ],
                };
                resolve(detailedData);
            } else {
                resolve(null);
            }
        }, 300));
    },

    // MOCK APIs for Customer Dashboard
    getCustomerProfile(): Promise<any> {
        console.log("MOCK API: Fetching customer profile...");
        return new Promise(resolve => setTimeout(() => resolve(mockCustomerProfileData), 400));
    },

    updateCustomerProfile(profileData: object): Promise<any> {
        console.log("MOCK API: Updating customer profile with:", profileData);
        Object.assign(mockCustomerProfileData, profileData);
        return new Promise(resolve => setTimeout(() => resolve({ success: true, updatedData: profileData }), 500));
    },
    
    getCustomerDesigns(): Promise<any> {
        console.log("MOCK API: Fetching customer designs...");
        return new Promise(resolve => setTimeout(() => resolve([...mockCustomerDesignsData]), 700));
    },

    getDesignById(designId: string): Promise<any> {
        console.log(`MOCK API: Fetching design ${designId}...`);
        return new Promise(resolve => setTimeout(() => resolve(mockCustomerDesignsData.find(d => d.id === designId)), 200));
    },

    deleteCustomerDesign(designId: string): Promise<any> {
        console.log(`MOCK API: Deleting customer design ${designId}`);
        mockCustomerDesignsData = mockCustomerDesignsData.filter(d => d.id !== designId);
        return new Promise(resolve => setTimeout(() => resolve({ success: true, designId }), 300));
    },

    getCustomerOrders(): Promise<any> {
        console.log("MOCK API: Fetching customer orders...");
        return new Promise(resolve => setTimeout(() => resolve(mockCustomerOrdersData), 600));
    },
};

// --- SVG Icons ---
const iconStyle = { width: '48px', height: '48px', color: 'currentColor', marginBottom: '16px' };
const ArrowLeftIcon = ({ style }: {style?: React.CSSProperties}) => (<svg style={style} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" /></svg>);
const UploadIcon = ({ style = iconStyle }: {style?: React.CSSProperties}) => (<svg xmlns="http://www.w3.org/2000/svg" style={style} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg>);
const QuoteIcon = ({ style = iconStyle }: {style?: React.CSSProperties}) => (<svg xmlns="http://www.w3.org/2000/svg" style={style} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>);
const ManufactureIcon = ({ style = iconStyle }: {style?: React.CSSProperties}) => (<svg xmlns="http://www.w3.org/2000/svg" style={style} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.096 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>);
const FileIcon = () => (<svg xmlns="http://www.w3.org/2000/svg" style={{ width: '48px', height: '48px', color: 'currentColor' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>);
const ShieldCheckIcon = ({ style = iconStyle }: {style?: React.CSSProperties}) => (<svg style={style} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.286zm0 13.036h.008v.008h-.008v-.008z" /></svg>);
const GlobeAltIcon = ({ style = iconStyle }: {style?: React.CSSProperties}) => (<svg style={style} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418" /></svg>);
const ScaleIcon = ({ style = iconStyle }: {style?: React.CSSProperties}) => (<svg style={style} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M12 3v17.25m0 0c-1.472 0-2.882.265-4.185.75M12 20.25c1.472 0 2.882.265 4.185.75M18.75 4.97A48.416 48.416 0 0012 4.5c-2.291 0-4.545.16-6.75.47m13.5 0c1.01.143 2.01.317 3 .52m-3-.52l2.62 10.726c.122.499-.106 1.028-.589 1.202a5.988 5.988 0 01-2.036.243c-2.132 0-4.14-.818-5.62-2.247m0 0a5.988 5.988 0 01-1.358-.853m-3.426 0l2.62 10.726c.122.499.106 1.028-.013 1.202a5.988 5.988 0 01-2.036.243c-2.132 0-4.14-.818-5.62-2.247m0 0l5.23-2.162m-3.426 0l-5.23 2.162" /></svg>);
const LightningBoltIcon = ({ style = iconStyle }: {style?: React.CSSProperties}) => (<svg style={style} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" /></svg>);
const CodeBracketIcon = ({ style = {...iconStyle, width: '32px', height: '32px'} }: {style?: React.CSSProperties}) => (<svg style={style} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M14.25 9.75L16.5 12l-2.25 2.25m-4.5 0L7.5 12l2.25-2.25M6 20.25h12A2.25 2.25 0 0020.25 18V6A2.25 2.25 0 0018 3.75H6A2.25 2.25 0 003.75 6v12A2.25 2.25 0 006 20.25z" /></svg>);
const WrenchScrewdriverIcon = ({ style = {...iconStyle, width: '32px', height: '32px'} }: {style?: React.CSSProperties}) => (<svg style={style} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M11.42 15.17L17.25 21A2.652 2.652 0 0021 17.25l-5.877-5.877M11.42 15.17l2.496-3.03c.317-.384.74-.626 1.208-.766M11.42 15.17l-4.655 5.653a2.548 2.548 0 11-3.586-3.586l6.837-5.63m5.108-.233c.55-.164 1.163-.188 1.743-.14a4.5 4.5 0 004.474-4.474c-.047-.58-.198-1.198-.44-1.743m-2.948 12.006c-.184-.183-.383-.355-.595-.515m0 0c-.212-.16-.44-.305-.678-.426m0 0l-5.877-5.877m5.877 5.877l-5.877-5.877M9.75 15.75l3-3M3.75 7.5h3m-3 3h3m-3 3h3m3.75 3.75h3m-3-3h3m-3-3h3m-3-3h3" /></svg>);
const TwitterIcon = ({style = {height: '24px', width: '24px'}}) => (<svg style={style} fill="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.71v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84" /></svg>);
const GithubIcon = ({style = {height: '24px', width: '24px'}}) => (<svg style={style} fill="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path fillRule="evenodd" d="M12 2C6.477 2 2 6.477 2 12c0 4.418 2.865 8.165 6.839 9.49.5.092.682-.217.682-.482 0-.237-.009-.868-.014-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.031-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.203 2.398.1 2.651.64.7 1.03 1.595 1.03 2.688 0 3.848-2.338 4.695-4.566 4.942.359.308.678.92.678 1.855 0 1.338-.012 2.419-.012 2.745 0 .267.18.577.688.48A10.005 10.005 0 0022 12c0-5.523-4.477-10-10-10z" clipRule="evenodd" /></svg>);
const LinkedInIcon = ({style = {height: '24px', width: '24px'}}) => (<svg style={style} fill="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path fillRule="evenodd" d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" clipRule="evenodd"/></svg>);
const SearchIcon = ({style}) => (<svg style={style} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>);
const LocationMarkerIcon = ({style}) => (<svg style={style} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>);
const StarIcon = ({style}) => (<svg style={style} xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"></path></svg>);
const BuildingOfficeIcon = ({style}) => (<svg style={style} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M8.25 21h7.5M12 3v18m0 0l-3.75-3.75M12 21l3.75-3.75" /></svg>);
const XMarkIcon = ({style}) => (<svg style={style} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>);
const ChartPieIcon = ({style}) => (<svg style={style} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M10.5 6a7.5 7.5 0 107.5 7.5h-7.5V6z" /><path strokeLinecap="round" strokeLinejoin="round" d="M13.5 10.5H21A7.5 7.5 0 0013.5 3v7.5z" /></svg>);
const UserCircleIcon = ({style}) => (<svg style={style} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M17.982 18.725A7.488 7.488 0 0012 15.75a7.488 7.488 0 00-5.982 2.975m11.963 0a9 9 0 10-11.963 0m11.963 0A8.966 8.966 0 0112 21a8.966 8.966 0 01-5.982-2.275M15 9.75a3 3 0 11-6 0 3 3 0 016 0z" /></svg>);
const DocumentTextIcon = ({style}) => (<svg style={style} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" /></svg>);
const CogIcon = ({style}) => (<svg style={style} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12a7.5 7.5 0 0015 0m-15 0a7.5 7.5 0 1115 0m-15 0H3m18 0h-1.5m-15 0a7.5 7.5 0 1115 0m-15 0H3m18 0h-1.5m-15 0a7.5 7.5 0 1115 0m-15 0H3m18 0h-1.5" /></svg>);
const CubeIcon = ({style}) => (<svg style={style} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M21 7.5l-9-5.25L3 7.5m18 0l-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9" /></svg>);
const ArchiveBoxIcon = ({style}) => (<svg style={style} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" /></svg>);
const VideoCameraIcon = ({style}) => (<svg style={style} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9A2.25 2.25 0 0013.5 5.25h-9A2.25 2.25 0 002.25 7.5v9A2.25 2.25 0 004.5 18.75z" /></svg>);

// --- Reusable Components ---

type CtaButtonProps = {
    text: string; href?: string; onClick?: (e?: React.MouseEvent) => void; primary?: boolean; type?: 'button' | 'submit' | 'reset'; children?: React.ReactNode; disabled?: boolean; className?: string;
};

const CtaButton = ({ text, href = "#", onClick, primary = false, type = "button", children, disabled = false, className = '' }: CtaButtonProps) => {
    const [hover, setHover] = useState(false);
    const variantStyle = primary ? styles.buttonPrimary : styles.buttonSecondary;
    const hoverStyle = primary && !disabled ? styles.buttonPrimaryHover : !disabled ? styles.buttonSecondaryHover : {};
    const disabledStyle = disabled ? styles.buttonDisabled : {};
    
    // Special danger button style
    const dangerStyle = className.includes('button-small-danger') ? styles.buttonDanger : {};
    const dangerHoverStyle = className.includes('button-small-danger') && !disabled ? styles.buttonDangerHover : {};

    const style = { ...styles.button, ...variantStyle, ...(hover ? hoverStyle : {}), ...dangerStyle, ...(hover ? dangerHoverStyle : {}), ...disabledStyle };
    const commonProps = { style: style, onMouseEnter: () => setHover(true), onMouseLeave: () => setHover(false), disabled: disabled, className: className };

    if (type === 'submit' || type === 'reset' || onClick) {
        return (<button type={type} onClick={onClick} {...commonProps}>{children}{text}</button>);
    }
    return (<a href={href} {...commonProps}>{children}{text}</a>);
};


const CheckboxGroup = ({ title, options, selected, onChange, columns = 3 }) => (
    <div style={styles.formGroup}>
        {title && <label style={styles.subLegend}>{title}</label>}
        <div style={{ ...styles.checkboxGrid, gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
            {options.map(option => (
                <label key={option} style={styles.checkboxLabel}>
                    <input type="checkbox" style={styles.checkboxInput} checked={selected.includes(option)} onChange={() => onChange(option)} />
                    {option}
                </label>
            ))}
        </div>
    </div>
);

const Notification = ({ message, type = 'success', onDismiss }) => {
    const baseStyle = {
        padding: '16px',
        borderRadius: '8px',
        margin: '16px 0',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        border: '1px solid',
    };
    const typeStyles = {
        success: { backgroundColor: 'rgba(16, 185, 129, 0.1)', color: '#10B981', borderColor: '#10B981', textShadow: '0 0 5px #10B981' },
        error: { backgroundColor: 'rgba(239, 68, 68, 0.1)', color: '#EF4444', borderColor: '#EF4444', textShadow: '0 0 5px #EF4444' },
    };
    return (
        <div style={{ ...baseStyle, ...typeStyles[type] }}>
            <span>{message}</span>
            <button onClick={onDismiss} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit' }}>
                <XMarkIcon style={{ width: '20px', height: '20px' }} />
            </button>
        </div>
    );
};

const FileViewerModal = ({ design, onClose }) => {
    if (!design || !design.files) return null;

    const { primary, supporting } = design.files;

    return (
        <div style={styles.modalBackdrop}>
            <div style={{...styles.modalContent, maxWidth: '700px'}}>
                <div style={styles.modalHeader}>
                    <h3 style={styles.modalTitle}>Files for: {design.name}</h3>
                    <button onClick={onClose} style={styles.modalCloseButton}><XMarkIcon style={{width: '24px', height: '24px'}} /></button>
                </div>
                <div style={styles.modalBody}>
                    <div style={{marginBottom: '24px'}}>
                        <h4 style={styles.subLegend}>Primary CAD File</h4>
                        <div style={styles.fileListItem}>
                             <CubeIcon style={{width: '24px', height: '24px', color: '#0AF0F0', flexShrink: 0}} />
                             <div style={styles.fileInfo}>
                                <span style={styles.fileName}>{primary.name}</span>
                                <span style={styles.fileSize}>{primary.size}</span>
                             </div>
                             <CtaButton text="Download" onClick={() => console.log('Downloading', primary.name)} />
                        </div>
                    </div>
                    {supporting && supporting.length > 0 && (
                         <div>
                            <h4 style={styles.subLegend}>Supporting Documents</h4>
                            <div style={{display: 'flex', flexDirection: 'column', gap: '12px'}}>
                            {supporting.map((file, index) => (
                                <div key={index} style={styles.fileListItem}>
                                    <DocumentTextIcon style={{width: '24px', height: '24px', color: '#E0E7FF', flexShrink: 0}} />
                                    <div style={styles.fileInfo}>
                                        <span style={styles.fileName}>{file.name}</span>
                                        <span style={styles.fileSize}>{file.size}</span>
                                    </div>
                                    <CtaButton text="Download" onClick={() => console.log('Downloading', file.name)} />
                                </div>
                            ))}
                            </div>
                        </div>
                    )}
                     <div style={styles.modalFooter}>
                        <CtaButton text="Close" primary onClick={onClose} />
                    </div>
                </div>
            </div>
        </div>
    );
};

const ImageUpload = ({ label, currentImageUrl, onImageSelected, onImageRemoved }) => {
    const inputRef = useRef(null);
    const [preview, setPreview] = useState(currentImageUrl);

    useEffect(() => {
        setPreview(currentImageUrl);
    }, [currentImageUrl]);

    const handleFileChange = (e) => {
        const file = e.target.files?.[0];
        if (file) {
            const previewUrl = URL.createObjectURL(file);
            setPreview(previewUrl);
            onImageSelected(file);
        }
    };
    
    const handleRemove = (e) => {
        e.stopPropagation();
        setPreview(null);
        onImageRemoved();
        if(inputRef.current) inputRef.current.value = "";
    };

    return (
        <div style={styles.formGroup}>
            <label style={styles.label}>{label}</label>
            <input type="file" accept="image/*" ref={inputRef} onChange={handleFileChange} style={{display: 'none'}} />
            <div style={styles.imageUploadBox} onClick={() => inputRef.current?.click()}>
                {preview ? (
                    <>
                        <img src={preview} alt="Preview" style={styles.imageUploadPreview} />
                        <button type="button" onClick={handleRemove} style={styles.imageUploadRemoveBtn} aria-label="Remove image">
                            <XMarkIcon style={{width: '16px', height: '16px'}} />
                        </button>
                    </>
                ) : (
                    <div style={styles.imageUploadPlaceholder}>
                        <UploadIcon style={{width: '32px', height: '32px', color: '#94A3B8', marginBottom: '8px'}} />
                        <span style={{fontSize: '14px', color: '#94A3B8'}}>Click to upload</span>
                    </div>
                )}
            </div>
        </div>
    );
};


// --- Page Sections ---

type HeaderProps = { isAuthenticated: boolean; onLogout: () => void; onNavigate: (page: string, params?: any) => void; };
const Header = ({ isAuthenticated, onLogout, onNavigate }: HeaderProps) => {
    const [hoveredLink, setHoveredLink] = useState('');
    return(
        <header style={styles.header} role="banner">
            <div style={styles.container}>
                <div style={styles.headerContent}>
                    <a href="#" style={styles.logo} onClick={(e) => { e.preventDefault(); onNavigate('landing'); }}>GMQP</a>
                    <nav style={styles.nav} role="navigation" aria-label="Main Navigation">
                        {[{id: 'how-it-works-detailed', text: 'How It Works'}, {id: 'directory', text: 'Manufacturer Directory'}].map(page => (
                            <a key={page.id} href="#" style={{...styles.navLink, ...(hoveredLink === page.id && styles.navLinkHover)}} onClick={(e) => { e.preventDefault(); onNavigate(page.id); }} onMouseEnter={() => setHoveredLink(page.id)} onMouseLeave={() => setHoveredLink('')}>
                                {page.text}
                            </a>
                        ))}
                    </nav>
                    <div style={styles.headerActions}>
                        {isAuthenticated ? (
                            <>
                                 <a href="#" style={{...styles.navLink, ...(hoveredLink === 'dashboard' && styles.navLinkHover)}} onMouseEnter={() => setHoveredLink('dashboard')} onMouseLeave={() => setHoveredLink('')} onClick={(e) => { e.preventDefault(); onNavigate('dashboard'); }}>My Dashboard</a>
                                 <CtaButton text="Log Out" onClick={onLogout} />
                            </>
                        ) : (
                            <>
                                <a href="#" style={{...styles.navLink, ...(hoveredLink === 'login' && styles.navLinkHover)}} onMouseEnter={() => setHoveredLink('login')} onMouseLeave={() => setHoveredLink('')} onClick={(e) => { e.preventDefault(); onNavigate('login'); }}>Log In</a>
                                <CtaButton text="Get Started" primary onClick={() => onNavigate('signup')} />
                            </>
                        )}
                    </div>
                </div>
            </div>
        </header>
    );
};

const Hero = ({ onNavigate }: { onNavigate: (page: string, params?: any) => void }) => (
    <section style={styles.hero}>
        <div style={{...styles.container, position: 'relative', zIndex: 1}}>
            <div style={styles.heroContent}>
                <h1 style={styles.heroTitle}>From Design to Production, Faster Than Ever.</h1>
                <p style={styles.heroSubtitle}>Get instant quotes from a global network of vetted manufacturers. Upload your design and compare prices, lead times, and quality in one place.</p>
                <div style={styles.heroActions}>
                    <CtaButton text="Get an Instant Quote" primary onClick={() => onNavigate('upload')} />
                    <CtaButton text="Join as a Manufacturer" onClick={() => onNavigate('signup-manufacturer')} />
                </div>
            </div>
        </div>
    </section>
);

const HowItWorks = () => (
    <section style={styles.howItWorks}>
        <div style={styles.container}>
            <h2 style={styles.sectionTitle}>Get Your Parts Made in 3 Simple Steps</h2>
            <div style={styles.stepsGrid}>
                <div style={styles.step}><UploadIcon style={{...iconStyle, color: '#0AF0F0'}} /><h3 style={styles.stepTitle}>1. Upload Your Design</h3><p style={styles.stepText}>Securely upload your CAD files (STEP, IGES, STL, etc.) and specify your requirements.</p></div>
                <div style={styles.step}><QuoteIcon style={{...iconStyle, color: '#0AF0F0'}} /><h3 style={styles.stepTitle}>2. Compare Instant Quotes</h3><p style={styles.stepText}>Our AI engine provides instant pricing. Compare quotes from suppliers based on cost, lead time, and ratings.</p></div>
                <div style={styles.step}><ManufactureIcon style={{...iconStyle, color: '#0AF0F0'}} /><h3 style={styles.stepTitle}>3. Order and Manufacture</h3><p style={styles.stepText}>Accept your preferred quote to start production. Track your order until it's delivered to your door.</p></div>
            </div>
        </div>
    </section>
);

const ValueProposition = () => {
    const [hoveredCard, setHoveredCard] = useState<number|null>(null);
    const valueProps = [
        { icon: <LightningBoltIcon />, title: "Instant Estimations", text: "Stop waiting. Our automated engine provides rapid cost estimates for your designs." },
        { icon: <GlobeAltIcon />, title: "Global Network", text: "Access a diverse, global pool of vetted manufacturers for any process." },
        { icon: <ScaleIcon />, title: "Informed Decisions", text: "Compare suppliers side-by-side on price, lead time, MOQ, and quality ratings." },
        { icon: <ShieldCheckIcon />, title: "IP Protection", text: "Your designs are secure. We prioritize robust protection for your intellectual property." },
    ];

    return (
        <section style={styles.features}>
            <div style={styles.container}>
                <h2 style={styles.sectionTitle}>The Smartest Way to Manufacture</h2>
                <div style={styles.valueGrid}>
                    {valueProps.map((prop, index) => (
                        <div key={index} style={{...styles.valueCard, ...(hoveredCard === index && styles.valueCardHover)}} onMouseEnter={() => setHoveredCard(index)} onMouseLeave={() => setHoveredCard(null)}>
                            {React.cloneElement(prop.icon, { style: {...iconStyle, color: hoveredCard === index ? '#0AF0F0' : '#F005B4'} })}
                            <h3 style={styles.stepTitle}>{prop.title}</h3>
                            <p style={styles.stepText}>{prop.text}</p>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
};

const ForWhom = ({ onNavigate }: { onNavigate: (page: string, params?: any) => void }) => (
    <section style={styles.howItWorks}>
        <div style={styles.container}>
            <div style={styles.forWhomGrid}>
                <div style={styles.forWhomCard}>
                    <div style={{display: 'flex', alignItems: 'center', gap: '16px'}}><CodeBracketIcon style={{...styles.forWhomIcon, color: '#0AF0F0'}} /><h3 style={styles.featureTitle}>For Engineers & Designers</h3></div>
                    <p style={styles.forWhomText}>Tired of manual searches and slow quote turnaround? Streamline your procurement process, reduce time-to-market, and find the perfect manufacturing partner without the hassle.</p>
                    <ul style={styles.featureList}><li>✓ Fast & Competitive Quotes</li><li>✓ Global Network of Suppliers</li><li>✓ Secure IP Protection</li><li>✓ Streamlined Ordering</li></ul>
                    <CtaButton text="Get an Instant Quote" primary onClick={() => onNavigate('upload')} />
                </div>
                <div style={styles.forWhomCard}>
                    <div style={{display: 'flex', alignItems: 'center', gap: '16px'}}><WrenchScrewdriverIcon style={{...styles.forWhomIcon, color: '#F005B4'}} /><h3 style={styles.featureTitle}>For Manufacturers</h3></div>
                     <p style={styles.forWhomText}>Access a global customer base, streamline your quoting workflow, and fill your production capacity. Let us bring the jobs to you so you can focus on what you do best: making things.</p>
                     <ul style={styles.featureList}><li>✓ Access a New Stream of Orders</li><li>✓ Automate Your Quoting Process</li><li>✓ Reduce Administrative Overhead</li><li>✓ Grow Your Business</li></ul>
                    <CtaButton text="Join Our Network" onClick={() => onNavigate('signup-manufacturer')} />
                </div>
            </div>
        </div>
    </section>
);

const SocialProof = () => (
    <section style={styles.features}>
        <div style={styles.container}>
            <h2 style={styles.sectionTitle}>Trusted by Innovators Worldwide</h2>
            <div style={styles.socialProofGrid}>
                <div style={styles.testimonialCard}><p style={styles.testimonialText}>"The instant quoting engine is a game-changer. We cut our sourcing time by 90% and got our product to market weeks ahead of schedule."</p><p style={styles.testimonialAuthor}>- Sarah J., Lead Engineer at Innovate Robotics</p></div>
                <div style={styles.testimonialCard}><p style={styles.testimonialText}>"Joining the GMQP network filled our excess capacity within three months. The quality of the incoming jobs is excellent."</p><p style={styles.testimonialAuthor}>- Mike P., Owner of Precision Parts Co.</p></div>
            </div>
            <div style={styles.metricsContainer}>
                <div style={styles.metricItem}><span style={styles.metricValue}>500+</span><span style={styles.metricLabel}>Manufacturers on Platform</span></div>
                <div style={styles.metricItem}><span style={styles.metricValue}>10,000+</span><span style={styles.metricLabel}>Parts Quoted</span></div>
                <div style={styles.metricItem}><span style={styles.metricValue}>42</span><span style={styles.metricLabel}>Countries Served</span></div>
            </div>
        </div>
    </section>
);

const PlaceholderPage = ({title, subtitle}) => (
     <div style={{...styles.container, padding: '96px 24px', textAlign: 'center', flexGrow: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
        <h1 style={{...styles.heroTitle, fontSize: '48px'}}>{title}</h1>
        <p style={{...styles.heroSubtitle, fontSize: '18px'}}>{subtitle}</p>
        <p style={{color: '#94A3B8'}}>This page is under construction. Check back soon for more updates!</p>
    </div>
);

const TrustAndSecurityPage = () => (
    <div style={{...styles.container, padding: '64px 24px'}}>
        <div style={{maxWidth: '800px', margin: '0 auto', textAlign: 'center'}}>
            <ShieldCheckIcon style={{ width: '64px', height: '64px', color: '#0AF0F0', marginBottom: '24px', filter: 'drop-shadow(0 0 10px #0AF0F0)' }} />
            <h1 style={styles.heroTitle}>Trust & Security</h1>
            <p style={styles.heroSubtitle}>Your intellectual property and data are our top priority. Learn about the measures we take to keep you secure.</p>
        </div>
        <div style={{maxWidth: '800px', margin: '48px auto 0', textAlign: 'left', display: 'flex', flexDirection: 'column', gap: '32px'}}>
            <div style={styles.featureCard}><h3 style={styles.featureTitle}>Intellectual Property (IP) Protection</h3><p style={styles.stepText}>We understand that your designs are your most valuable asset. Our platform is built with multiple layers of security to ensure your IP is protected from the moment you upload it.</p><ul style={{...styles.featureList, marginTop: '16px', listStyle: 'disc', paddingLeft: '20px', gap: '8px'}}><li><strong>Secure Uploads:</strong> All file transfers are encrypted using industry-standard SSL/TLS protocols.</li><li><strong>Access Control:</strong> Your design files are only accessible to you and the manufacturers you choose to request quotes from.</li><li><strong>In-Browser 3D Viewer:</strong> Manufacturers can inspect your 3D models securely in their browser without downloading the source file, preventing unauthorized distribution.</li><li><strong>Integrated NDAs:</strong> We facilitate standardized Non-Disclosure Agreements that you can execute with manufacturers directly on the platform before sharing sensitive details.</li></ul></div>
            <div style={styles.featureCard}><h3 style={styles.featureTitle}>Manufacturer Vetting & Quality Assurance</h3><p style={styles.stepText}>We maintain a high-quality network by carefully vetting every manufacturer who joins our platform. This ensures you're working with professional and reliable partners.</p><ul style={{...styles.featureList, marginTop: '16px', listStyle: 'disc', paddingLeft: '20px', gap: '8px'}}><li><strong>Verification Process:</strong> We verify the business information and operational history of all manufacturers.</li><li><strong>Capability Audits:</strong> We review manufacturer-submitted information about their equipment, processes, and certifications.</li><li><strong>Community Reviews:</strong> Our transparent review system allows you to see ratings and feedback from other customers before placing an order.</li></ul></div>
            <div style={styles.featureCard}><h3 style={styles.featureTitle}>Secure Payments & Transactions</h3><p style={styles.stepText}>Our platform ensures that financial transactions are secure and transparent, protecting both customers and manufacturers.</p><ul style={{...styles.featureList, marginTop: '16px', listStyle: 'disc', paddingLeft: '20px', gap: '8px'}}><li><strong>Secure Payment Gateway:</strong> We partner with leading payment processors to handle all transactions securely. Your financial data is never stored on our servers.</li><li><strong>Escrow System (Coming Soon):</strong> We plan to implement an escrow system where payments are held securely and released to the manufacturer upon reaching agreed-upon project milestones.</li><li><strong>Clear Dispute Resolution:</strong> We provide a structured process to mediate and resolve any disputes related to payments or order fulfillment.</li></ul></div>
        </div>
    </div>
);

const LandingPageContent = ({ onNavigate }: { onNavigate: (page: string) => void }) => (
    <><Hero onNavigate={onNavigate} /><HowItWorks /><ValueProposition /><ForWhom onNavigate={onNavigate} /><SocialProof /></>
);

type FooterProps = { onNavigate: (page: string, params?: any) => void; };
const Footer = ({ onNavigate }: FooterProps) => (
    <footer style={styles.footer} role="contentinfo">
        <div style={styles.container}>
             <div style={styles.footerGrid}>
                 <div style={styles.footerColumn}><h3 style={styles.footerHeading}>Platform</h3><a href="#" style={styles.footerLink} onClick={(e) => { e.preventDefault(); onNavigate('how-it-works-detailed'); }}>How It Works</a><a href="#" style={styles.footerLink} onClick={(e) => { e.preventDefault(); onNavigate('directory'); }}>Manufacturer Directory</a><a href="#" style={styles.footerLink} onClick={(e) => { e.preventDefault(); onNavigate('trust-and-security'); }}>Trust & Security</a></div>
                 <div style={styles.footerColumn}><h3 style={styles.footerHeading}>Company</h3><a href="#" style={styles.footerLink} onClick={(e) => { e.preventDefault(); onNavigate('about'); }}>About Us</a><a href="#" style={styles.footerLink} onClick={(e) => { e.preventDefault(); onNavigate('blog'); }}>Blog</a><a href="#" style={styles.footerLink} onClick={(e) => { e.preventDefault(); onNavigate('contact'); }}>Contact Us</a></div>
                 <div style={styles.footerColumn}><h3 style={styles.footerHeading}>Resources</h3><a href="#" style={styles.footerLink} onClick={(e) => { e.preventDefault(); onNavigate('faq'); }}>FAQ</a><a href="#" style={styles.footerLink}>Help Center</a></div>
                 <div style={styles.footerColumn}><h3 style={styles.footerHeading}>Legal</h3><a href="#" style={styles.footerLink} onClick={(e) => { e.preventDefault(); onNavigate('privacy'); }}>Privacy Policy</a><a href="#" style={styles.footerLink} onClick={(e) => { e.preventDefault(); onNavigate('terms'); }}>Terms of Service</a></div>
             </div>
             <div style={styles.footerBottom}>
                <p style={styles.footerCopyright}>© {new Date().getFullYear()} Global Manufacturing Quotation Platform. All rights reserved.</p>
                <div style={styles.footerSocials}><a href="#" style={styles.footerSocialLink} aria-label="Twitter"><TwitterIcon/></a><a href="#" style={styles.footerSocialLink} aria-label="GitHub"><GithubIcon/></a><a href="#" style={styles.footerSocialLink} aria-label="LinkedIn"><LinkedInIcon/></a></div>
             </div>
        </div>
    </footer>
);

// --- Login/Signup Pages ---

const SignupRoleSelector = ({ onNavigate }: { onNavigate: (page: string, params?: any) => void }) => (
    <div style={styles.loginPage}><div style={styles.loginContainer}><h2 style={styles.loginTitle}>Join GMQP</h2><p style={styles.loginSubtitle}>Select your account type to get started.</p><div style={{display: 'flex', flexDirection: 'column', gap: '16px', marginTop: '32px'}}><CtaButton text="Sign Up as a Customer" primary onClick={() => onNavigate('signup-customer')} /><CtaButton text="Sign Up as a Manufacturer" onClick={() => onNavigate('signup-manufacturer')} /></div><div style={{textAlign: 'center', marginTop: '24px'}}><p style={{color: '#94A3B8', fontSize: '14px'}}>Already have an account? <a href="#" style={{...styles.loginLink, fontSize: '14px'}} onClick={(e) => { e.preventDefault(); onNavigate('login'); }}>Log In</a></p></div></div></div>
);

const CustomerSignupPage = ({ onLogin, onNavigate }: { onLogin: (credentials: object, role: string) => Promise<void>, onNavigate: (page: string) => void }) => {
    const [companyName, setCompanyName] = useState(''); const [email, setEmail] = useState(''); const [password, setPassword] = useState(''); const [password2, setPassword2] = useState(''); const [error, setError] = useState(''); const [loading, setLoading] = useState(false);
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (password !== password2) { setError('Passwords do not match.'); return; }
        setError(''); setLoading(true);
        try {
            await api.register({ email, password, password2, company_name: companyName, role: 'customer' });
            await onLogin({ email, password }, 'customer');
        } catch (err) { setError(err.message); setLoading(false); }
    };
    return (
        <div style={styles.loginPage}><div style={styles.loginContainer}><h2 style={styles.loginTitle}>Create Customer Account</h2><p style={styles.loginSubtitle}>Get instant quotes from top manufacturers.</p><form onSubmit={handleSubmit} style={styles.loginForm}>{error && <p style={styles.loginError}>{error}</p>}<div style={styles.formGroup}><label htmlFor="companyName" style={styles.label}>Company Name</label><input type="text" id="companyName" value={companyName} onChange={(e) => setCompanyName(e.target.value)} style={styles.input} required /></div><div style={styles.formGroup}><label htmlFor="email" style={styles.label}>Email Address</label><input type="email" id="email" value={email} onChange={(e) => setEmail(e.target.value)} style={styles.input} required autoComplete="email" /></div><div style={styles.formGroup}><label htmlFor="password" style={styles.label}>Password</label><input type="password" id="password" value={password} onChange={(e) => setPassword(e.target.value)} style={styles.input} required autoComplete="new-password" /></div><div style={styles.formGroup}><label htmlFor="password2" style={styles.label}>Confirm Password</label><input type="password" id="password2" value={password2} onChange={(e) => setPassword2(e.target.value)} style={styles.input} required autoComplete="new-password" /></div><CtaButton text={loading ? "Creating Account..." : "Create Account"} primary type="submit" disabled={loading} /></form><div style={styles.loginLinks}><a href="#" style={styles.loginLink} onClick={(e) => { e.preventDefault(); onNavigate('signup'); }}>Back to role selection</a></div></div></div>
    );
};

const ManufacturerSignupPage = ({ onLogin, onNavigate }: { onLogin: (credentials: object, role: string) => Promise<void>, onNavigate: (page: string) => void }) => {
    const [formData, setFormData] = useState({ companyName: '', email: '', password: '', password2: '', location: '', website: '', productionVolume: '', leadTimeRange: '', certifications: [], otherCertifications: '', qualityControlProcesses: '', materialTesting: '', moq: '', machining: [], sheetMetal: [], casting: [], forging: [], injectionMolding: { processes: [], cavityCount: '', moldClass: '' }, threeDPrinting: [], weldingJoining: [], supportedMaterials: [], generalTolerance: '', specificTolerances: '', gdtSupport: false, minSizeX: '', minSizeY: '', minSizeZ: '', maxSizeX: '', maxSizeY: '', maxSizeZ: '', maxWeightKg: '', thinWallCapabilityMm: '', surfaceFinishes: [], postProcessing: [], acceptedFileFormats: [], incoterms: [], specialCapabilities: [], });
    const [error, setError] = useState(''); const [loading, setLoading] = useState(false);
    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
        const { name, value, type } = e.target;
        if (type === 'checkbox') { const { checked } = e.target as HTMLInputElement; setFormData(prev => ({ ...prev, [name]: checked })); } else { setFormData(prev => ({ ...prev, [name]: value })); }
    };
    const handleInjectionMoldingChange = (e: React.ChangeEvent<HTMLInputElement>) => { const { name, value } = e.target; setFormData(prev => ({ ...prev, injectionMolding: { ...prev.injectionMolding, [name]: value } })); };
    const handleCheckboxGroupChange = (category, value) => {
        if (category === 'injectionMoldingProcesses') {
            setFormData(prev => { const list = prev.injectionMolding.processes || []; const newList = list.includes(value) ? list.filter(item => item !== value) : [...list, value]; return { ...prev, injectionMolding: { ...prev.injectionMolding, processes: newList } }; });
        } else { setFormData(prev => { const list = (prev[category] as string[]) || []; const newList = list.includes(value) ? list.filter(item => item !== value) : [...list, value]; return { ...prev, [category]: newList }; }); }
    };
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault(); setError(''); setLoading(true);
        const { password, password2, companyName, email, location, productionVolume, leadTimeRange, moq, machining, sheetMetal, casting, forging, injectionMolding, threeDPrinting, weldingJoining, supportedMaterials } = formData;
        if (password !== password2) { setLoading(false); return setError('Passwords do not match.'); }
        if (!companyName || !email || !password || !location || !productionVolume || !leadTimeRange || !moq) { setLoading(false); return setError('Please fill all required fields in Account, Profile, and General Capabilities.'); }
        const totalProcesses = [...machining, ...sheetMetal, ...casting, ...forging, ...injectionMolding.processes, ...threeDPrinting, ...weldingJoining].length;
        if (totalProcesses === 0) { setLoading(false); return setError('Please select at least one Manufacturing Process.'); }
        if (supportedMaterials.length === 0) { setLoading(false); return setError('Please select at least one supported Material.'); }
        try {
            await api.register({ email, password, password2, company_name: companyName, role: 'manufacturer' });
            const { access, refresh } = await api.login({ email, password });
            setTokens(access, refresh);
            const profileData = { location: formData.location, website_url: formData.website, certifications: [...formData.certifications, ...formData.otherCertifications.split(',').map(s => s.trim()).filter(Boolean)], capabilities: { cnc: formData.machining.length > 0 || formData.sheetMetal.length > 0, materials_supported: formData.supportedMaterials, max_size_mm: [ formData.maxSizeX ? Number(formData.maxSizeX) : null, formData.maxSizeY ? Number(formData.maxSizeY) : null, formData.maxSizeZ ? Number(formData.maxSizeZ) : null, ], } };
            await api.updateManufacturerProfile(profileData);
            await onLogin({ email, password }, 'manufacturer');
        } catch (err) { setError(err.message); setLoading(false); }
    };
    const manufacturerSignupContainerStyle = { ...styles.loginContainer, maxWidth: '900px' };

    return (
        <div style={styles.loginPage}><div style={manufacturerSignupContainerStyle}><h2 style={styles.loginTitle}>Create Manufacturer Account</h2><p style={styles.loginSubtitle}>Join our network and start receiving orders. Fields marked with * are required.</p><form onSubmit={handleSubmit}>{error && <p style={styles.loginError}>{error}</p>}<fieldset style={styles.fieldset}><legend style={styles.legend}>Account & Profile</legend><div style={styles.formRow}><div style={styles.formGroup}><label htmlFor="companyName" style={styles.label}>Company Name *</label><input type="text" name="companyName" value={formData.companyName} onChange={handleInputChange} style={styles.input} required /></div><div style={styles.formGroup}><label htmlFor="email" style={styles.label}>Email Address *</label><input type="email" name="email" value={formData.email} onChange={handleInputChange} style={styles.input} required autoComplete="email" /></div></div><div style={styles.formRow}><div style={styles.formGroup}><label htmlFor="password" style={styles.label}>Password *</label><input type="password" name="password" value={formData.password} onChange={handleInputChange} style={styles.input} required autoComplete="new-password" /></div><div style={styles.formGroup}><label htmlFor="password2" style={styles.label}>Confirm Password *</label><input type="password" name="password2" value={formData.password2} onChange={handleInputChange} style={styles.input} required autoComplete="new-password" /></div></div><div style={styles.formRow}><div style={styles.formGroup}><label htmlFor="location" style={styles.label}>Location (City, Country) *</label><input type="text" name="location" value={formData.location} onChange={handleInputChange} style={styles.input} required /></div><div style={styles.formGroup}><label htmlFor="website" style={styles.label}>Website URL</label><input type="url" name="website" value={formData.website} onChange={handleInputChange} style={styles.input} placeholder="https://yourcompany.com" /></div></div></fieldset><fieldset style={styles.fieldset}><legend style={styles.legend}>1. General Capabilities *</legend><div style={styles.formRow}><div style={styles.formGroup}><label htmlFor="productionVolume" style={styles.label}>Production Volume Capacity *</label><select name="productionVolume" value={formData.productionVolume} onChange={handleInputChange} style={styles.input} required><option value="">Select volume...</option>{PRODUCTION_VOLUMES.map(v => <option key={v} value={v}>{v}</option>)}</select></div><div style={styles.formGroup}><label htmlFor="leadTimeRange" style={styles.label}>Typical Lead Time Range *</label><input type="text" name="leadTimeRange" value={formData.leadTimeRange} onChange={handleInputChange} style={styles.input} required placeholder="e.g., 5-10 days" /></div></div><div style={styles.formRow}><div style={styles.formGroup}><label htmlFor="moq" style={styles.label}>Minimum Order Quantity (MOQ) *</label><input type="number" name="moq" value={formData.moq} onChange={handleInputChange} style={styles.input} required min="0"/></div><div style={styles.formGroup}><label htmlFor="otherCertifications" style={styles.label}>Other Certs (comma-separated)</label><input type="text" name="otherCertifications" value={formData.otherCertifications} onChange={handleInputChange} style={styles.input} /></div></div><CheckboxGroup title="Certifications" options={CERTIFICATIONS} selected={formData.certifications} onChange={(v) => handleCheckboxGroupChange('certifications', v)} /><div style={styles.formGroup}><label htmlFor="qualityControlProcesses" style={styles.label}>Quality Control Processes</label><textarea name="qualityControlProcesses" value={formData.qualityControlProcesses} onChange={handleInputChange} style={styles.input} rows={3}></textarea></div><div style={styles.formGroup}><label htmlFor="materialTesting" style={styles.label}>Material Testing / Inspection Equipment</label><textarea name="materialTesting" value={formData.materialTesting} onChange={handleInputChange} style={styles.input} rows={3}></textarea></div></fieldset><fieldset style={styles.fieldset}><legend style={styles.legend}>2. Manufacturing Processes Supported *</legend><p style={styles.fieldsetDescription}>Select all that apply. You must select at least one process.</p>{ALL_CAPABILITIES_GROUPS.map(group => <CheckboxGroup key={group.title} title={group.title} options={group.processes} selected={formData[group.title.toLowerCase().replace(/ & /g, 'and').replace(/ /g, '')] || []} onChange={(v) => handleCheckboxGroupChange(group.title.toLowerCase().replace(/ & /g, 'and').replace(/ /g, ''), v)} /> )}</fieldset><fieldset style={styles.fieldset}><legend style={styles.legend}>3. Material Capabilities *</legend><p style={styles.fieldsetDescription}>You must select at least one material.</p><CheckboxGroup title="Metals" options={MATERIALS_METALS} selected={formData.supportedMaterials} onChange={(v) => handleCheckboxGroupChange('supportedMaterials', v)} /><CheckboxGroup title="Plastics" options={MATERIALS_PLASTICS} selected={formData.supportedMaterials} onChange={(v) => handleCheckboxGroupChange('supportedMaterials', v)} /><CheckboxGroup title="Composites" options={MATERIALS_COMPOSITES} selected={formData.supportedMaterials} onChange={(v) => handleCheckboxGroupChange('supportedMaterials', v)} /><CheckboxGroup title="Others" options={MATERIALS_OTHERS} selected={formData.supportedMaterials} onChange={(v) => handleCheckboxGroupChange('supportedMaterials', v)} /></fieldset><div style={{marginTop: '24px'}}><CtaButton text={loading ? "Creating Account..." : "Create Account & Go to Dashboard"} primary type="submit" disabled={loading}/></div></form><div style={styles.loginLinks}><a href="#" style={styles.loginLink} onClick={(e) => { e.preventDefault(); onNavigate('signup'); }}>Back to role selection</a></div></div></div>
    );
};

const LoginPage = ({ onLogin, onNavigate, role }) => {
    const [email, setEmail] = useState(''); const [password, setPassword] = useState(''); const [error, setError] = useState(''); const [loading, setLoading] = useState(false);
    const isCustomer = role === 'customer';
    const title = isCustomer ? "Customer Sign In" : "Manufacturer Sign In";
    const subtitle = isCustomer ? "Access your account to manage your designs and orders." : "Access your dashboard to manage quotes and production.";
    const signupText = isCustomer ? "Don't have an account? Sign Up" : "Want to join our network? Apply here";
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault(); setLoading(true); setError('');
        try { await onLogin({ email, password }, role); } catch (err) { setError(err.message); setLoading(false); }
    };
    return (<div style={styles.loginPage}><div style={styles.loginContainer}><h2 style={styles.loginTitle}>{title}</h2><p style={styles.loginSubtitle}>{subtitle}</p><form onSubmit={handleSubmit} style={styles.loginForm}>{error && <p style={styles.loginError}>{error}</p>}<div style={styles.formGroup}><label htmlFor="email" style={styles.label}>Email Address</label><input type="email" id="email" value={email} onChange={(e) => setEmail(e.target.value)} style={styles.input} required autoComplete="email"/></div><div style={styles.formGroup}><label htmlFor="password" style={styles.label}>Password</label><input type="password" id="password" value={password} onChange={(e) => setPassword(e.target.value)} style={styles.input} required autoComplete="current-password"/></div><CtaButton text={loading ? "Signing In..." : "Sign In"} primary type="submit" disabled={loading}/></form><div style={styles.loginLinks}><a href="#" style={{...styles.loginLink}} onClick={(e) => { e.preventDefault(); }}>Forgot password?</a><a href="#" style={styles.loginLink} onClick={(e) => { e.preventDefault(); onNavigate('signup'); }}>{signupText}</a></div></div></div>);
};

const LoginRoleSelector = ({ onNavigate, reasonMessage }: { onNavigate: (page: string) => void, reasonMessage?: string }) => (
    <div style={styles.loginPage}><div style={styles.loginContainer}>{reasonMessage && <p style={styles.loginReasonMessage}>{reasonMessage}</p>}<h2 style={styles.loginTitle}>Sign In</h2><p style={styles.loginSubtitle}>Please select your role to continue.</p><div style={{display: 'flex', flexDirection: 'column', gap: '16px', marginTop: '32px'}}><CtaButton text="I'm a Customer" primary onClick={() => onNavigate('login-customer')} /><CtaButton text="I'm a Manufacturer" onClick={() => onNavigate('login-manufacturer')} /></div><div style={{textAlign: 'center', marginTop: '24px'}}><p style={{color: '#94A3B8', fontSize: '14px'}}>New to GMQP? <a href="#" style={{...styles.loginLink, fontSize: '14px'}} onClick={(e) => { e.preventDefault(); onNavigate('signup'); }}>Create an account</a></p><p style={{marginTop: '16px'}}><a href="#" style={{...styles.loginLink, color: '#94A3B8', fontSize: '14px'}} onClick={(e) => { e.preventDefault(); onNavigate('landing'); }}>← Back to Homepage</a></p></div></div></div>
);

// --- Dashboard & Upload Components ---

const UploadPage = ({ onProceedToLogin, onNavigate }) => {
    const [formData, setFormData] = useState({
        designName: '',
        material: '',
        quantity: '',
        manufacturingProcess: '',
        surfaceFinish: 'None',
        tolerances: '',
        postProcessing: [],
        additionalInstructions: '',
        requiredCertifications: '',
        shippingDestination: '',
        targetPrice: '',
    });
    const [file, setFile] = useState<File | null>(null);
    const [supportingFiles, setSupportingFiles] = useState<File[]>([]);
    const [isDragging, setIsDragging] = useState(false);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const supportingFilesInputRef = useRef<HTMLInputElement>(null);

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handlePostProcessingChange = (option: string) => {
        setFormData(prev => {
            const { postProcessing } = prev;
            const newPostProcessing = postProcessing.includes(option)
                ? postProcessing.filter(item => item !== option)
                : [...postProcessing, option];
            return { ...prev, postProcessing: newPostProcessing };
        });
    };

    const handleDragOver = (e: React.DragEvent) => { e.preventDefault(); e.stopPropagation(); setIsDragging(true); };
    const handleDragLeave = (e: React.DragEvent) => { e.preventDefault(); e.stopPropagation(); setIsDragging(false); };
    const handleDrop = (e: React.DragEvent) => { e.preventDefault(); e.stopPropagation(); setIsDragging(false); if (e.dataTransfer.files && e.dataTransfer.files.length > 0) { setFile(e.dataTransfer.files[0]); setError(''); e.dataTransfer.clearData(); } };
    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => { if (e.target.files && e.target.files.length > 0) { setFile(e.target.files[0]); setError(''); } };
    
    const handleSupportingFilesChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            setSupportingFiles(prev => [...prev, ...Array.from(e.target.files)]);
            if (e.target) e.target.value = null; // Allow selecting the same file again
        }
    };

    const removeSupportingFile = (indexToRemove: number) => {
        setSupportingFiles(prev => prev.filter((_, index) => index !== indexToRemove));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        if (!file) {
            setError('Please select a primary CAD file to upload.');
            return;
        }
        if (!formData.designName || !formData.manufacturingProcess || !formData.material || !formData.quantity) {
            setError('Please fill all required fields (*).');
            return;
        }
        setLoading(true);
        onProceedToLogin({ file, supportingFiles, ...formData });
    };

    const dropzoneStyle = { ...styles.uploadDropzone, ...(isDragging ? styles.uploadDropzoneActive : {}), };
    
    return (<div style={styles.uploadPageContainer}><div style={styles.dashboardHeader}><h1 style={styles.dashboardTitle}>Get an Instant Quote</h1></div><p style={{...styles.loginSubtitle, textAlign: 'left', marginTop: '-16px', marginBottom: '32px'}}>Step 1 of 2: Specify design details and upload your CAD file.</p><form onSubmit={handleSubmit}>{error && <p style={styles.loginError}>{error}</p>}<div style={styles.uploadLayout}><div style={styles.uploadDropzoneWrapper}><label style={styles.label}>Primary CAD File (.stl, .step, .iges) *</label><div style={dropzoneStyle} onDragEnter={e => e.stopPropagation()} onDragOver={handleDragOver} onDragLeave={handleDragLeave} onDrop={handleDrop} onClick={() => fileInputRef.current?.click()}><input type="file" ref={fileInputRef} onChange={handleFileChange} style={{ display: 'none' }} accept=".stl,.step,.iges,.stp" />{file ? (<div style={styles.uploadFileInfo}><FileIcon /><p style={styles.uploadFileName}>{file.name}</p><p style={{fontSize: '12px', color: '#94A3B8'}}>{(file.size / 1024).toFixed(2)} KB</p><CtaButton text="Clear" onClick={(e) => { e.stopPropagation(); setFile(null); }} type="button" /></div>) : (<><UploadIcon style={{...iconStyle, width: '64px', height: '64px', color: '#94A3B8' }}/><p style={{color: '#E0E7FF', fontWeight: 500}}>Drag & drop file here</p><p style={{color: '#94A3B8', fontSize: '14px'}}>or click to browse</p></>)}</div></div><div style={styles.uploadFormFields}><div style={styles.formGroup}><label htmlFor="designName" style={styles.label}>Design Name *</label><input type="text" id="designName" name="designName" value={formData.designName} onChange={handleInputChange} style={styles.input} required placeholder="e.g., Main Housing Unit" /></div><div style={styles.formGroup}><label htmlFor="quantity" style={styles.label}>Quantity *</label><input type="text" id="quantity" name="quantity" value={formData.quantity} onChange={handleInputChange} style={styles.input} required list="quantity-options" placeholder="e.g., 25 or select a range" /><datalist id="quantity-options"><option value="1-10 (Prototypes)"></option><option value="11-50 (Small Batch)"></option><option value="51-250 (Low Volume)"></option><option value="251-1000 (Medium Volume)"></option><option value="1000+ (High Volume)"></option></datalist></div><div style={styles.formGroup}><label htmlFor="manufacturingProcess" style={styles.label}>Manufacturing Process *</label><select id="manufacturingProcess" name="manufacturingProcess" value={formData.manufacturingProcess} onChange={handleInputChange} style={styles.input} required><option value="">Select a process...</option>{ALL_CAPABILITIES_GROUPS.map(group => (<optgroup label={group.title} key={group.title}>{group.processes.map(process => <option key={process} value={process}>{process}</option>)}</optgroup>))}</select></div><div style={styles.formGroup}><label htmlFor="material" style={styles.label}>Material *</label><select id="material" name="material" value={formData.material} onChange={handleInputChange} style={styles.input} required><option value="">Select a material...</option><optgroup label="Plastics">{MATERIALS_PLASTICS.map(m => <option key={m} value={m}>{m}</option>)}</optgroup><optgroup label="Metals">{MATERIALS_METALS.map(m => <option key={m} value={m}>{m}</option>)}</optgroup><optgroup label="Composites">{MATERIALS_COMPOSITES.map(m => <option key={m} value={m}>{m}</option>)}</optgroup><optgroup label="Other">{MATERIALS_OTHERS.map(m => <option key={m} value={m}>{m}</option>)}</optgroup></select></div><div style={styles.formGroup}><label htmlFor="surfaceFinish" style={styles.label}>Surface Finish</label><select id="surfaceFinish" name="surfaceFinish" value={formData.surfaceFinish} onChange={handleInputChange} style={styles.input}><option value="None">None</option>{SURFACE_FINISHES.map(f => <option key={f} value={f}>{f}</option>)}</select></div><div style={styles.formGroup}><label htmlFor="tolerances" style={styles.label}>Tolerances (if any)</label><input type="text" id="tolerances" name="tolerances" value={formData.tolerances} onChange={handleInputChange} style={styles.input} placeholder="e.g., +/- 0.05mm on critical features" /></div><CheckboxGroup title="Post-Processing (Optional)" options={POST_PROCESSING_ASSEMBLY} selected={formData.postProcessing} onChange={handlePostProcessingChange} columns={2}/>
                    
                    <fieldset style={{...styles.fieldset, marginTop: '24px', padding: '24px', backgroundColor: 'transparent', border: `1px solid rgba(175, 200, 255, 0.15)`}}>
                        <legend style={{...styles.legend, padding: '0 8px'}}>Supporting Information (Optional)</legend>
                        
                        <div style={styles.formGroup}>
                            <label style={styles.label}>Supporting Documents & Models</label>
                            <p style={{fontSize: '12px', color: '#94A3B8', margin: '-4px 0 8px 0'}}>Add technical drawings (PDF, DXF), secondary models, or other relevant files.</p>
                            <input type="file" multiple ref={supportingFilesInputRef} onChange={handleSupportingFilesChange} style={{ display: 'none' }} accept=".pdf,.dxf,.step,.stp,.iges,.igs,.zip,.rar,.sldprt,.dwg" />
                            <CtaButton text="Add Files" onClick={() => supportingFilesInputRef.current?.click()} type="button" />
                            {supportingFiles.length > 0 && (
                                <div style={styles.supportingFileList}>
                                    {supportingFiles.map((f, index) => (
                                        <div key={`${f.name}-${index}`} style={styles.supportingFileItem}>
                                            <DocumentTextIcon style={{width: '20px', height: '20px', color: '#94A3B8', flexShrink: 0, marginRight: '8px'}} />
                                            <span style={styles.supportingFileName} title={f.name}>{f.name}</span>
                                            <button type="button" onClick={() => removeSupportingFile(index)} style={styles.supportingFileRemoveBtn} aria-label={`Remove ${f.name}`}>
                                                <XMarkIcon style={{width: '16px', height: '16px'}} />
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        <div style={{...styles.formGroup, marginTop: '20px'}}>
                            <label htmlFor="additionalInstructions" style={styles.label}>Additional Instructions or Comments</label>
                            <textarea id="additionalInstructions" name="additionalInstructions" value={formData.additionalInstructions} onChange={handleInputChange} style={styles.input} rows={4} placeholder="e.g., Critical tolerances on hole diameters. Please deburr all sharp edges. See attached PDF for finishing requirements." />
                        </div>
                        <div style={{...styles.formGroup, marginTop: '20px'}}>
                            <label htmlFor="requiredCertifications" style={styles.label}>Required Certifications</label>
                            <input type="text" id="requiredCertifications" name="requiredCertifications" value={formData.requiredCertifications} onChange={handleInputChange} style={styles.input} placeholder="e.g., ISO 9001, Material Certs"/>
                        </div>
                        <div style={{...styles.formGroup, marginTop: '20px'}}>
                            <label htmlFor="shippingDestination" style={styles.label}>Shipping Destination</label>
                            <input type="text" id="shippingDestination" name="shippingDestination" value={formData.shippingDestination} onChange={handleInputChange} style={styles.input} placeholder="e.g., Austin, TX, USA"/>
                        </div>
                        <div style={{...styles.formGroup, marginTop: '20px'}}>
                            <label htmlFor="targetPrice" style={styles.label}>Target Price per Part</label>
                            <input type="text" id="targetPrice" name="targetPrice" value={formData.targetPrice} onChange={handleInputChange} style={styles.input} placeholder="e.g., $15.50 (optional)"/>
                        </div>
                    </fieldset>
                    
                    <div style={{ marginTop: '32px' }}>
                        <CtaButton text={loading ? "Processing..." : "Proceed to Login"} primary type="submit" disabled={loading} />
                    </div>
                </div></div></form></div>);
};

// --- Manufacturer Directory & Profile Pages ---
const ManufacturerCard = ({ manufacturer, onNavigate }) => {
    const [hover, setHover] = useState(false);
    return (
        <div style={{...styles.mfgCard, ...(hover && styles.mfgCardHover)}} onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)} onClick={() => onNavigate('manufacturer-profile', manufacturer.id)}>
            <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '16px'}}>
                 <img src={manufacturer.logoUrl} alt={`${manufacturer.company_name} logo`} style={styles.mfgCardLogo} />
                <div style={{flex: 1}}>
                    <h3 style={styles.mfgCardTitle}>{manufacturer.company_name}</h3>
                    <p style={styles.mfgCardLocation}>
                        <LocationMarkerIcon style={{width: '16px', height: '16px', marginRight: '4px', color: '#94A3B8', flexShrink: 0}}/>
                        {manufacturer.location}
                    </p>
                </div>
                <div style={{display: 'flex', alignItems: 'center', gap: '4px', color: '#FFD700'}}>
                    <StarIcon style={{width: '16px', height: '16px', filter: 'drop-shadow(0 0 3px #FFD700)'}} />
                    <span style={{fontWeight: 'bold', color: '#E0E7FF'}}>{manufacturer.rating.toFixed(1)}</span>
                </div>
            </div>
            
            <div style={{marginTop: '16px'}}>
                <h4 style={styles.mfgCardSectionTitle}>Key Capabilities</h4>
                <div style={styles.mfgCardTagContainer}>
                    {manufacturer.capabilities.slice(0, 3).map(cap => <span key={cap} style={styles.mfgCardTag}>{cap}</span>)}
                    {manufacturer.capabilities.length > 3 && <span style={styles.mfgCardTag}>+{manufacturer.capabilities.length - 3} more</span>}
                </div>
            </div>
             <div style={{marginTop: '16px'}}>
                <h4 style={styles.mfgCardSectionTitle}>Certifications</h4>
                 <div style={styles.mfgCardTagContainer}>
                    {manufacturer.certifications.length > 0 ? (
                        manufacturer.certifications.map(cert => <span key={cert} style={{...styles.mfgCardTag, ...styles.mfgCardCertTag}}>{cert}</span>)
                    ) : (
                        <span style={{fontSize: '12px', color: '#94A3B8'}}>None listed</span>
                    )}
                </div>
            </div>
            <div style={{marginTop: '24px', textAlign: 'center'}}>
                 <span style={{...styles.mfgCardViewProfileLink, ...(hover && styles.mfgCardViewProfileLinkHover)}}>View Profile →</span>
            </div>
        </div>
    );
};

const ManufacturerDirectoryPage = ({ onNavigate }) => {
    const [manufacturers, setManufacturers] = useState([]);
    const [filteredManufacturers, setFilteredManufacturers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedCapabilities, setSelectedCapabilities] = useState([]);
    const [selectedCertifications, setSelectedCertifications] = useState([]);

    useEffect(() => {
        const fetchManufacturers = async () => {
            try {
                const data = await api.getManufacturers();
                if (Array.isArray(data)) {
                    setManufacturers(data);
                    setFilteredManufacturers(data);
                } else {
                    setError('Received invalid data for manufacturers.');
                }
            } catch (err) {
                setError('Failed to load manufacturers.');
            } finally {
                setLoading(false);
            }
        };
        fetchManufacturers();
    }, []);

    useEffect(() => {
        let results = manufacturers;
        if (searchTerm) {
            results = results.filter(m => m.company_name.toLowerCase().includes(searchTerm.toLowerCase()));
        }
        if (selectedCapabilities.length > 0) {
            results = results.filter(m => selectedCapabilities.every(cap => m.capabilities.includes(cap)));
        }
        if (selectedCertifications.length > 0) {
            results = results.filter(m => selectedCertifications.every(cert => m.certifications.includes(cert)));
        }
        setFilteredManufacturers(results);
    }, [searchTerm, selectedCapabilities, selectedCertifications, manufacturers]);

    const handleCapabilityChange = (capability) => {
        setSelectedCapabilities(prev => prev.includes(capability) ? prev.filter(c => c !== capability) : [...prev, capability]);
    };
    
    const handleCertificationChange = (certification) => {
        setSelectedCertifications(prev => prev.includes(certification) ? prev.filter(c => c !== certification) : [...prev, certification]);
    };

    return (
        <div style={{...styles.container, padding: '64px 24px'}}>
            <div style={{textAlign: 'center'}}>
                <h1 style={styles.heroTitle}>Manufacturer Directory</h1>
                <p style={styles.heroSubtitle}>Find the perfect partner for your manufacturing needs.</p>
            </div>
            <div style={styles.directoryLayout}>
                <aside style={styles.directoryFilters}>
                    <h2 style={{fontSize: '20px', fontWeight: '600', color: '#E0E7FF', borderBottom: '1px solid rgba(175, 200, 255, 0.15)', paddingBottom: '16px'}}>Filters</h2>
                    <div style={styles.searchContainer}>
                        <SearchIcon style={{position: 'absolute', left: '12px', top: '12px', width: '20px', height: '20px', color: '#94A3B8'}}/>
                        <input 
                            type="text" 
                            placeholder="Search by name..." 
                            value={searchTerm}
                            onChange={e => setSearchTerm(e.target.value)}
                            style={styles.searchInput} 
                        />
                    </div>
                    <div style={{marginTop: '24px'}}>
                        <CheckboxGroup title="Capabilities" options={ALL_CAPABILITIES_FLAT.slice(0, 9)} selected={selectedCapabilities} onChange={handleCapabilityChange} columns={1}/>
                        {ALL_CAPABILITIES_FLAT.length > 9 && <a href="#" style={{...styles.loginLink, fontSize: '14px'}}>Show all...</a>}
                    </div>
                     <div style={{marginTop: '24px'}}>
                        <CheckboxGroup title="Certifications" options={CERTIFICATIONS} selected={selectedCertifications} onChange={handleCertificationChange} columns={1}/>
                    </div>
                </aside>
                <main style={styles.directoryResults}>
                    {loading ? (
                        <p>Loading manufacturers...</p>
                    ) : error ? (
                        <p style={{color: 'red'}}>{error}</p>
                    ) : filteredManufacturers.length > 0 ? (
                        <div style={styles.mfgGrid}>
                            {filteredManufacturers.map(mfg => <ManufacturerCard key={mfg.id} manufacturer={mfg} onNavigate={onNavigate} />)}
                        </div>
                    ) : (
                        <div style={{textAlign: 'center', padding: '64px', border: '2px dashed rgba(175, 200, 255, 0.15)', borderRadius: '8px'}}>
                            <h3 style={{color: '#E0E7FF'}}>No Manufacturers Found</h3>
                            <p style={{color: '#94A3B8'}}>Try adjusting your search or filter criteria.</p>
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
};

const ManufacturerProfilePage = ({ manufacturerId, onNavigate }) => {
    const [manufacturer, setManufacturer] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        if (!manufacturerId) {
            setError('No manufacturer ID provided.');
            setLoading(false);
            return;
        }
        const fetchManufacturer = async () => {
            setLoading(true);
            try {
                const data = await api.getManufacturerById(manufacturerId);
                if (data) {
                    setManufacturer(data);
                } else {
                    setError('Manufacturer not found.');
                }
            } catch (err) {
                setError('Failed to load manufacturer details.');
            } finally {
                setLoading(false);
            }
        };
        fetchManufacturer();
    }, [manufacturerId]);

    const getCapabilitiesByGroup = () => {
        if (!manufacturer?.capabilities) return [];
        return ALL_CAPABILITIES_GROUPS.map(group => ({
            title: group.title,
            processes: group.processes.filter(p => manufacturer.capabilities.includes(p))
        })).filter(g => g.processes.length > 0);
    };

    if (loading) return <div style={{...styles.container, padding: '64px 24px', textAlign: 'center'}}>Loading profile...</div>;
    if (error) return <div style={{...styles.container, padding: '64px 24px', textAlign: 'center', color: 'red'}}>{error}</div>;
    if (!manufacturer) return <div style={{...styles.container, padding: '64px 24px', textAlign: 'center'}}>Manufacturer profile could not be loaded.</div>;

    const capabilityGroups = getCapabilitiesByGroup();
    const materials = manufacturer.capabilities.filter(c => [...MATERIALS_METALS, ...MATERIALS_PLASTICS, ...MATERIALS_COMPOSITES, ...MATERIALS_OTHERS].includes(c));

    const profileHeaderStyle: React.CSSProperties = {
        ...styles.profileHeader,
        backgroundImage: `linear-gradient(rgba(2, 4, 10, 0.7), rgba(2, 4, 10, 0.7)), url(${manufacturer.backgroundUrl})`,
    };

    return (
        <div style={styles.profilePageContainer}>
            <header style={profileHeaderStyle}>
                <div style={styles.container}>
                    <button onClick={() => onNavigate('directory')} style={styles.backButton}>
                        <ArrowLeftIcon style={{width: '20px', height: '20px', marginRight: '8px'}} />
                        Back to Directory
                    </button>
                    <div style={styles.profileHeaderContent}>
                        <img src={manufacturer.logoUrl} alt={`${manufacturer.company_name} logo`} style={styles.profileHeaderLogo} />
                        <div style={{flex: 1}}>
                            <h1 style={styles.profileTitle}>{manufacturer.company_name}</h1>
                            <p style={styles.profileLocation}>
                                <LocationMarkerIcon style={{width: '18px', height: '18px', marginRight: '6px'}}/>
                                {manufacturer.location}
                            </p>
                        </div>
                        <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
                            <StarIcon style={{width: '28px', height: '28px', color: '#FFD700', filter: 'drop-shadow(0 0 5px #FFD700)'}} />
                            <span style={{fontSize: '28px', fontWeight: 'bold', color: '#FFFFFF', textShadow: '0 1px 3px rgba(0,0,0,0.5)'}}>{manufacturer.rating.toFixed(1)}</span>
                        </div>
                    </div>
                </div>
            </header>
            <div style={styles.container}>
                <div style={styles.profileContentGrid}>
                    <main style={styles.profileMainContent}>
                        <section style={styles.profileSection}>
                            <h2 style={styles.profileSectionTitle}>About {manufacturer.company_name}</h2>
                            <p style={styles.stepText}>{manufacturer.about}</p>
                        </section>
                         <section style={styles.profileSection}>
                            <h2 style={styles.profileSectionTitle}>Project Portfolio</h2>
                            <div style={styles.profilePortfolioGrid}>
                                {manufacturer.portfolio.map(item => (
                                    <div key={item.id} style={styles.portfolioItem}>
                                        {item.type === 'video' ? (
                                            <div style={styles.portfolioVideoPlaceholder}>
                                                <VideoCameraIcon style={{width: '48px', height: '48px', color: '#fff'}} />
                                            </div>
                                        ) : (
                                            <img src={item.url} alt={item.title} style={styles.profilePortfolioImage} />
                                        )}
                                        <div style={styles.portfolioItemOverlay}>
                                            <p style={styles.portfolioItemTitle}>{item.title}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </section>
                        <section style={styles.profileSection}>
                            <h2 style={styles.profileSectionTitle}>Customer Reviews</h2>
                            <div style={{display: 'flex', flexDirection: 'column', gap: '16px'}}>
                                {manufacturer.reviews.map(review => (
                                    <div key={review.id} style={{border: `1px solid rgba(175, 200, 255, 0.15)`, backgroundColor: 'rgba(2, 4, 10, 0.5)', borderRadius: '8px', padding: '16px'}}>
                                        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px'}}>
                                            <p style={{fontWeight: 600, color: '#E0E7FF', margin: 0}}>{review.author}</p>
                                            <div style={{display: 'flex', gap: '2px', color: '#FFD700'}}>
                                                {[...Array(review.rating)].map((_,i) => <StarIcon key={i} style={{width: '16px', height: '16px', filter: 'drop-shadow(0 0 2px #FFD700)'}}/>)}
                                                {[...Array(5-review.rating)].map((_,i) => <StarIcon key={i} style={{width: '16px', height: '16px', color: 'rgba(175, 200, 255, 0.2)'}}/>)}
                                            </div>
                                        </div>
                                        <p style={{...styles.stepText, fontSize: '14px'}}>{review.comment}</p>
                                    </div>
                                ))}
                            </div>
                        </section>
                    </main>
                    <aside style={styles.profileSidebar}>
                         <div style={{...styles.profileSection, border: '1px solid #0AF0F0', padding: '24px', background: 'rgba(10, 240, 240, 0.1)', textAlign: 'center', boxShadow: '0 0 15px rgba(10, 240, 240, 0.3)'}}>
                            <CtaButton text="Request Quote" primary onClick={() => onNavigate('upload')} className="button-full-width" />
                        </div>
                        <div style={styles.profileSection}>
                            <h2 style={styles.profileSectionTitle}>Capabilities</h2>
                            {capabilityGroups.map(group => (
                                <div key={group.title} style={{marginBottom: '16px'}}>
                                    <h3 style={styles.mfgCardSectionTitle}>{group.title}</h3>
                                    <div style={styles.mfgCardTagContainer}>
                                        {group.processes.map(p => <span key={p} style={styles.mfgCardTag}>{p}</span>)}
                                    </div>
                                </div>
                            ))}
                        </div>
                        <div style={styles.profileSection}>
                            <h2 style={styles.profileSectionTitle}>Certifications</h2>
                            <div style={styles.mfgCardTagContainer}>
                                {manufacturer.certifications.length > 0 ?
                                    manufacturer.certifications.map(c => <span key={c} style={{...styles.mfgCardTag, ...styles.mfgCardCertTag}}>{c}</span>)
                                    : <p style={styles.stepText}>No certifications listed.</p>}
                            </div>
                        </div>
                        <div style={styles.profileSection}>
                            <h2 style={styles.profileSectionTitle}>Materials</h2>
                             <div style={styles.mfgCardTagContainer}>
                                {materials.length > 0 ?
                                    materials.map(m => <span key={m} style={{...styles.mfgCardTag, ...styles.mfgCardMaterialTag}}>{m}</span>)
                                    : <p style={styles.stepText}>No materials specified.</p>}
                            </div>
                        </div>
                         <div style={styles.profileSection}>
                            <h2 style={styles.profileSectionTitle}>Equipment List</h2>
                             <ul style={{...styles.featureList, listStyle: 'disc', paddingLeft: '20px', gap: '8px', margin: 0}}>
                                {manufacturer.equipment.map(e => <li key={e}>{e}</li>)}
                            </ul>
                        </div>
                    </aside>
                </div>
            </div>
        </div>
    );
};

// --- Manufacturer Dashboard Components ---

const DashboardOverview = ({ user }) => (
    <div>
        <h2 style={styles.dashboardPageTitle}>Overview</h2>
        <p style={{ ...styles.stepText, fontSize: '18px' }}>Welcome back, {user?.company_name}!</p>
        <div style={styles.statsGrid}>
            <div style={styles.statCard}>
                <h3 style={styles.statValue}>5</h3>
                <p style={styles.statLabel}>New Quote Requests</p>
            </div>
            <div style={styles.statCard}>
                <h3 style={styles.statValue}>2</h3>
                <p style={styles.statLabel}>Active Orders</p>
            </div>
            <div style={styles.statCard}>
                <h3 style={styles.statValue}>$12,450</h3>
                <p style={styles.statLabel}>Revenue (This Month)</p>
            </div>
             <div style={styles.statCard}>
                <h3 style={styles.statValue}>98%</h3>
                <p style={styles.statLabel}>On-Time Delivery</p>
            </div>
        </div>
    </div>
);

const ManufacturerProfileManagementPage = () => {
    const [formData, setFormData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [notification, setNotification] = useState({ show: false, message: '', type: 'success' });
    const portfolioFileInputRef = useRef(null);

    useEffect(() => {
        const fetchProfile = async () => {
            try {
                const profile = await api.getManufacturerProfile();
                if (profile && typeof profile === 'object') {
                    const normalizedData = {
                        ...profile,
                        '3dPrinting': profile['3dPrinting'] || [],
                        portfolio: profile.portfolio || [],
                    };
                    setFormData(normalizedData);
                } else {
                    setError('Failed to load profile data or data is in wrong format.');
                }
            } catch (err) {
                setError('Failed to load profile data.');
            } finally {
                setLoading(false);
            }
        };
        fetchProfile();
    }, []);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleCheckboxGroupChange = (category, value) => {
        setFormData(prev => {
            const list = prev[category] || [];
            const newList = list.includes(value) ? list.filter(item => item !== value) : [...list, value];
            return { ...prev, [category]: newList };
        });
    };
    
    const handleImageChange = (field, file) => {
        // In a real app, you'd upload the file and get a URL.
        // For mock, we use a blob URL for preview.
        setFormData(prev => ({...prev, [field]: file ? URL.createObjectURL(file) : null}));
    }

    const handlePortfolioFilesChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (files) {
            const newItems = Array.from(files).map(file => ({
                id: Date.now() + Math.random(), // temporary unique id
                type: file.type.startsWith('video') ? 'video' : 'image',
                title: file.name.split('.')[0], // default title
                url: URL.createObjectURL(file) // for preview
            }));
            setFormData(prev => ({...prev, portfolio: [...prev.portfolio, ...newItems]}));
        }
    };
    
    const removePortfolioItem = (id) => {
        setFormData(prev => ({...prev, portfolio: prev.portfolio.filter(item => item.id !== id)}));
    };

    const handlePortfolioTitleChange = (id, newTitle) => {
        setFormData(prev => ({
            ...prev,
            portfolio: prev.portfolio.map(item => item.id === id ? {...item, title: newTitle} : item)
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setNotification({ show: false, message: '', type: 'success' });
        try {
            await api.updateManufacturerProfile(formData);
            setNotification({ show: true, message: 'Profile updated successfully!', type: 'success' });
        } catch (err) {
            setNotification({ show: true, message: err.message, type: 'error' });
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div>Loading profile...</div>;
    if (error) return <p style={styles.loginError}>{error}</p>;
    if (!formData) return <p>Could not load profile data.</p>;

    return (
        <div>
            <h2 style={styles.dashboardPageTitle}>Profile Management</h2>
            <p style={styles.dashboardPageSubtitle}>Keep your company profile and capabilities up to date to attract the right customers.</p>
            {notification.show && <Notification message={notification.message} type={notification.type} onDismiss={() => setNotification({ show: false, message: '', type: 'success' })} />}
            <form onSubmit={handleSubmit}>
                <fieldset style={{...styles.fieldset, marginTop: 0}}><legend style={styles.legend}>Company Information</legend><div style={styles.formRow}><div style={styles.formGroup}><label htmlFor="companyName" style={styles.label}>Company Name</label><input type="text" name="companyName" value={formData.companyName} onChange={handleInputChange} style={styles.input} required /></div><div style={styles.formGroup}><label htmlFor="email" style={styles.label}>Public Email Address</label><input type="email" name="email" value={formData.email} onChange={handleInputChange} style={styles.input} required /></div></div><div style={styles.formRow}><div style={styles.formGroup}><label htmlFor="location" style={styles.label}>Location (City, Country)</label><input type="text" name="location" value={formData.location} onChange={handleInputChange} style={styles.input} required /></div><div style={styles.formGroup}><label htmlFor="website" style={styles.label}>Website URL</label><input type="url" name="website" value={formData.website} onChange={handleInputChange} style={styles.input} placeholder="https://yourcompany.com" /></div></div></fieldset>
                
                <fieldset style={styles.fieldset}><legend style={styles.legend}>Branding & Appearance</legend><div style={styles.formRow}><ImageUpload label="Company Logo" currentImageUrl={formData.logoUrl} onImageSelected={(file) => handleImageChange('logoUrl', file)} onImageRemoved={() => handleImageChange('logoUrl', null)} /><ImageUpload label="Profile Background Image" currentImageUrl={formData.backgroundUrl} onImageSelected={(file) => handleImageChange('backgroundUrl', file)} onImageRemoved={() => handleImageChange('backgroundUrl', null)} /></div></fieldset>
                
                <fieldset style={styles.fieldset}>
                    <legend style={styles.legend}>Portfolio Management</legend>
                    <div style={styles.formGroup}>
                        <label style={styles.label}>Portfolio Items</label>
                        <p style={styles.fieldsetDescription}>Upload images or videos of your best work. Add a title for each item.</p>
                        <input type="file" multiple accept="image/*,video/*" ref={portfolioFileInputRef} onChange={handlePortfolioFilesChange} style={{display: 'none'}} />
                        <CtaButton text="Upload New Items" onClick={() => portfolioFileInputRef.current?.click()} type="button" />
                        
                        <div style={styles.portfolioManagementGrid}>
                            {formData.portfolio.map(item => (
                                <div key={item.id} style={styles.portfolioManagementItem}>
                                    {item.type === 'video' ? (
                                        <div style={styles.portfolioVideoPlaceholder}><VideoCameraIcon style={{width: '32px', height: '32px', color: '#fff'}} /></div>
                                    ) : (
                                        <img src={item.url} alt={item.title} style={styles.portfolioManagementImage} />
                                    )}
                                    <button type="button" onClick={() => removePortfolioItem(item.id)} style={styles.imageUploadRemoveBtn} aria-label={`Remove ${item.title}`}><XMarkIcon style={{width: '16px', height: '16px'}} /></button>
                                    <input type="text" value={item.title} onChange={(e) => handlePortfolioTitleChange(item.id, e.target.value)} style={styles.portfolioManagementTitleInput} placeholder="Enter title..." />
                                </div>
                            ))}
                        </div>
                    </div>
                </fieldset>

                <fieldset style={styles.fieldset}><legend style={styles.legend}>General Capabilities</legend><div style={styles.formRow}><div style={styles.formGroup}><label htmlFor="productionVolume" style={styles.label}>Production Volume Capacity</label><select name="productionVolume" value={formData.productionVolume} onChange={handleInputChange} style={styles.input} required><option value="">Select volume...</option>{PRODUCTION_VOLUMES.map(v => <option key={v} value={v}>{v}</option>)}</select></div><div style={styles.formGroup}><label htmlFor="leadTimeRange" style={styles.label}>Typical Lead Time Range</label><input type="text" name="leadTimeRange" value={formData.leadTimeRange} onChange={handleInputChange} style={styles.input} required placeholder="e.g., 5-10 days" /></div></div><div style={styles.formRow}><div style={styles.formGroup}><label htmlFor="moq" style={styles.label}>Minimum Order Quantity (MOQ)</label><input type="number" name="moq" value={formData.moq} onChange={handleInputChange} style={styles.input} required min="0"/></div><div style={styles.formGroup}><label htmlFor="otherCertifications" style={styles.label}>Other Certs (comma-separated)</label><input type="text" name="otherCertifications" value={formData.otherCertifications} onChange={handleInputChange} style={styles.input} /></div></div><CheckboxGroup title="Certifications" options={CERTIFICATIONS} selected={formData.certifications} onChange={(v) => handleCheckboxGroupChange('certifications', v)} /><div style={styles.formGroup}><label htmlFor="qualityControlProcesses" style={styles.label}>Quality Control Processes</label><textarea name="qualityControlProcesses" value={formData.qualityControlProcesses} onChange={handleInputChange} style={styles.input} rows={3}></textarea></div><div style={styles.formGroup}><label htmlFor="materialTesting" style={styles.label}>Material Testing / Inspection Equipment</label><textarea name="materialTesting" value={formData.materialTesting} onChange={handleInputChange} style={styles.input} rows={3}></textarea></div></fieldset>
                <fieldset style={styles.fieldset}><legend style={styles.legend}>Manufacturing Processes Supported</legend>{ALL_CAPABILITIES_GROUPS.map(group => <CheckboxGroup key={group.title} title={group.title} options={group.processes} selected={formData[group.title.toLowerCase().replace(/ & /g, 'and').replace(/ /g, '')] || []} onChange={(v) => handleCheckboxGroupChange(group.title.toLowerCase().replace(/ & /g, 'and').replace(/ /g, ''), v)} /> )}</fieldset>
                <fieldset style={styles.fieldset}><legend style={styles.legend}>Material Capabilities</legend><CheckboxGroup title="Metals" options={MATERIALS_METALS} selected={formData.supportedMaterials} onChange={(v) => handleCheckboxGroupChange('supportedMaterials', v)} /><CheckboxGroup title="Plastics" options={MATERIALS_PLASTICS} selected={formData.supportedMaterials} onChange={(v) => handleCheckboxGroupChange('supportedMaterials', v)} /><CheckboxGroup title="Composites" options={MATERIALS_COMPOSITES} selected={formData.supportedMaterials} onChange={(v) => handleCheckboxGroupChange('supportedMaterials', v)} /><CheckboxGroup title="Others" options={MATERIALS_OTHERS} selected={formData.supportedMaterials} onChange={(v) => handleCheckboxGroupChange('supportedMaterials', v)} /></fieldset>
                <div style={{marginTop: '24px'}}><CtaButton text={loading ? "Saving..." : "Save Changes"} primary type="submit" disabled={loading}/></div>
            </form>
        </div>
    );
};

const QuoteRequestModal = ({ request, onClose, onSubmit }) => {
    const [quoteData, setQuoteData] = useState({ price: '', leadTime: '', notes: '' });
    const [loading, setLoading] = useState(false);
    
    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setQuoteData(prev => ({ ...prev, [name]: value }));
    };
    
    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        await onSubmit(request.designId, quoteData);
        setLoading(false);
        onClose();
    };

    return (
        <div style={styles.modalBackdrop}>
            <div style={styles.modalContent}>
                <div style={styles.modalHeader}>
                    <h3 style={styles.modalTitle}>Quote Request: {request.designName}</h3>
                    <button onClick={onClose} style={styles.modalCloseButton}><XMarkIcon style={{width: '24px', height: '24px'}} /></button>
                </div>
                <div style={styles.modalBody}>
                    <div style={styles.quoteDetailsGrid}>
                        <div><p style={styles.quoteDetailLabel}>Customer</p><p style={styles.quoteDetailValue}>{request.customer}</p></div>
                        <div><p style={styles.quoteDetailLabel}>Material</p><p style={styles.quoteDetailValue}>{request.material}</p></div>
                        <div><p style={styles.quoteDetailLabel}>Quantity</p><p style={styles.quoteDetailValue}>{request.quantity}</p></div>
                        <div><p style={styles.quoteDetailLabel}>Surface Finish</p><p style={styles.quoteDetailValue}>{request.surfaceFinish}</p></div>
                    </div>
                     <div style={{borderTop: `1px solid rgba(175, 200, 255, 0.15)`, margin: '16px 0'}}></div>
                    <form onSubmit={handleSubmit}>
                        <div style={styles.formRow}>
                            <div style={styles.formGroup}>
                                <label htmlFor="price" style={styles.label}>Your Price (USD)</label>
                                <input type="number" name="price" value={quoteData.price} onChange={handleInputChange} style={styles.input} required placeholder="e.g., 150.75" />
                            </div>
                            <div style={styles.formGroup}>
                                <label htmlFor="leadTime" style={styles.label}>Lead Time (business days)</label>
                                <input type="number" name="leadTime" value={quoteData.leadTime} onChange={handleInputChange} style={styles.input} required placeholder="e.g., 10" />
                            </div>
                        </div>
                        <div style={styles.formGroup}>
                            <label htmlFor="notes" style={styles.label}>Notes (optional)</label>
                            <textarea name="notes" value={quoteData.notes} onChange={handleInputChange} style={styles.input} rows={3} placeholder="Add any notes for the customer..."></textarea>
                        </div>
                        <div style={styles.modalFooter}>
                            <CtaButton text="Cancel" onClick={onClose} />
                            <CtaButton text={loading ? "Submitting..." : "Submit Quote"} primary type="submit" disabled={loading} />
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};

const QuoteRequestsPage = ({ onViewFiles }) => {
    const [requests, setRequests] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [modalInfo, setModalInfo] = useState({ isOpen: false, request: null });
    const [notification, setNotification] = useState({ show: false, message: '', type: 'success' });
    
    useEffect(() => {
        fetchRequests();
    }, []);
    
    const fetchRequests = async () => {
        setLoading(true);
        try {
            const data = await api.getQuoteRequests();
            setRequests(data as any[]);
        } catch (err) {
            setError('Failed to load quote requests.');
        } finally {
            setLoading(false);
        }
    };
    
    const handleOpenModal = (request) => {
        setModalInfo({ isOpen: true, request: request });
    };

    const handleCloseModal = () => {
        setModalInfo({ isOpen: false, request: null });
    };

    const handleQuoteSubmit = async (designId, quoteData) => {
        await api.submitQuote(designId, quoteData);
        setNotification({ show: true, message: `Quote for ${modalInfo.request.designName} submitted successfully!`, type: 'success' });
        // Refresh the list to show updated status
        const updatedRequests = requests.map(r => r.id === modalInfo.request.id ? { ...r, status: 'Quoted' } : r);
        setRequests(updatedRequests);
    };
    
    const handleDecline = async (request) => {
        // Using confirm for simplicity. A custom modal would be better for UX.
        if (window.confirm(`Are you sure you want to decline the quote for "${request.designName}"?`)) {
            try {
                await api.declineQuoteRequest(request.designId);
                setNotification({ show: true, message: `Request for ${request.designName} declined.`, type: 'success' });
                const updatedRequests = requests.map(r => r.id === request.id ? { ...r, status: 'Declined' } : r);
                setRequests(updatedRequests);
            } catch(err) {
                 setNotification({ show: true, message: `Error declining request: ${err.message}`, type: 'error' });
            }
        }
    };

    const getStatusStyle = (status) => {
        const baseStyle = { ...styles.statusBadge };
        switch (status) {
            case 'Pending': return { ...baseStyle, color: '#FBBF24', backgroundColor: 'rgba(251, 191, 36, 0.1)', border: '1px solid rgba(251, 191, 36, 0.3)' };
            case 'Quoted': return { ...baseStyle, color: '#34D399', backgroundColor: 'rgba(52, 211, 153, 0.1)', border: '1px solid rgba(52, 211, 153, 0.3)' };
            case 'Declined': return { ...baseStyle, color: '#F87171', backgroundColor: 'rgba(248, 113, 113, 0.1)', border: '1px solid rgba(248, 113, 113, 0.3)' };
            default: return { ...baseStyle, color: '#94A3B8', backgroundColor: 'rgba(148, 163, 184, 0.1)', border: '1px solid rgba(148, 163, 184, 0.2)' };
        }
    };

    if (loading) return <div>Loading requests...</div>;
    if (error) return <p style={styles.loginError}>{error}</p>;

    return (
        <div>
            <h2 style={styles.dashboardPageTitle}>Quote Requests</h2>
            <p style={styles.dashboardPageSubtitle}>Review and respond to quote requests from customers.</p>
            {notification.show && <Notification message={notification.message} type={notification.type} onDismiss={() => setNotification({ show: false, message: '', type: 'success' })} />}
            <div style={styles.tableContainer}>
                <table style={styles.table}>
                    <thead>
                        <tr>
                            <th style={styles.tableHeader}>Part Name</th>
                            <th style={styles.tableHeader}>Customer</th>
                            <th style={styles.tableHeader}>Material</th>
                            <th style={styles.tableHeader}>Qty</th>
                            <th style={styles.tableHeader}>Date Received</th>
                            <th style={styles.tableHeader}>Status</th>
                            <th style={styles.tableHeader}>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {requests.map(req => (
                            <tr key={req.id}>
                                <td style={styles.tableCell}>{req.designName}</td>
                                <td style={styles.tableCell}>{req.customer}</td>
                                <td style={styles.tableCell}>{req.material}</td>
                                <td style={styles.tableCell}>{req.quantity}</td>
                                <td style={styles.tableCell}>{new Date(req.dateReceived).toLocaleDateString()}</td>
                                <td style={styles.tableCell}><span style={getStatusStyle(req.status)}>{req.status}</span></td>
                                <td style={styles.tableCell}>
                                    <div style={{display: 'flex', gap: '8px', alignItems: 'center'}}>
                                        <CtaButton text="View Files" onClick={() => onViewFiles(req.designId)} className="button-small" />
                                        {req.status === 'Pending' ? (
                                            <>
                                                <CtaButton text="Quote" primary onClick={() => handleOpenModal(req)} className="button-small" />
                                                <CtaButton text="Decline" onClick={() => handleDecline(req)} className="button-small-danger" />
                                            </>
                                        ) : (
                                            <span style={{color: '#94A3B8', fontSize: '14px'}}>Completed</span>
                                        )}
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            {modalInfo.isOpen && <QuoteRequestModal request={modalInfo.request} onClose={handleCloseModal} onSubmit={handleQuoteSubmit} />}
        </div>
    );
};

const UpdateOrderModal = ({ order, onClose, onUpdate }) => {
    const [formData, setFormData] = useState({
        status: order.status || '',
        trackingNumber: order.trackingNumber || '',
        shippingCarrier: order.shippingCarrier || '',
    });
    const [loading, setLoading] = useState(false);
    
    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };
    
    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        await onUpdate(order.id, formData);
        setLoading(false);
        onClose();
    };

    const isShipped = formData.status === 'Shipped' || formData.status === 'Delivered';

    return (
        <div style={styles.modalBackdrop}>
            <div style={{...styles.modalContent, maxWidth: '700px'}}>
                <div style={styles.modalHeader}>
                    <h3 style={styles.modalTitle}>Manage Order: {order.designName} ({order.id})</h3>
                    <button onClick={onClose} style={styles.modalCloseButton}><XMarkIcon style={{width: '24px', height: '24px'}} /></button>
                </div>
                <div style={styles.modalBody}>
                    <div style={styles.quoteDetailsGrid}>
                        <div><p style={styles.quoteDetailLabel}>Customer</p><p style={styles.quoteDetailValue}>{order.customer}</p></div>
                        <div><p style={styles.quoteDetailLabel}>Order Date</p><p style={styles.quoteDetailValue}>{new Date(order.dateCreated).toLocaleDateString()}</p></div>
                        <div><p style={styles.quoteDetailLabel}>Quantity</p><p style={styles.quoteDetailValue}>{order.quantity}</p></div>
                        <div><p style={styles.quoteDetailLabel}>Price</p><p style={styles.quoteDetailValue}>${order.quotePrice.toFixed(2)}</p></div>
                    </div>
                    <div style={{borderTop: `1px solid rgba(175, 200, 255, 0.15)`, margin: '16px 0'}}></div>
                    <form onSubmit={handleSubmit}>
                        <div style={styles.formGroup}>
                            <label htmlFor="status" style={styles.label}>Order Status</label>
                            <select name="status" id="status" value={formData.status} onChange={handleInputChange} style={styles.input} required>
                                {ORDER_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
                            </select>
                        </div>
                        {isShipped && (
                             <div style={{...styles.formRow, marginTop: '20px'}}>
                                <div style={styles.formGroup}>
                                    <label htmlFor="trackingNumber" style={styles.label}>Tracking Number</label>
                                    <input type="text" name="trackingNumber" value={formData.trackingNumber} onChange={handleInputChange} style={styles.input} placeholder="e.g., 1Z..." />
                                </div>
                                <div style={styles.formGroup}>
                                    <label htmlFor="shippingCarrier" style={styles.label}>Shipping Carrier</label>
                                    <input type="text" name="shippingCarrier" value={formData.shippingCarrier} onChange={handleInputChange} style={styles.input} placeholder="e.g., UPS, FedEx" />
                                </div>
                            </div>
                        )}
                        <div style={styles.modalFooter}>
                            <CtaButton text="Cancel" onClick={onClose} />
                            <CtaButton text={loading ? "Saving..." : "Save Changes"} primary type="submit" disabled={loading} />
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};

const ActiveOrdersPage = ({ onViewFiles }) => {
    const [orders, setOrders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [modalInfo, setModalInfo] = useState({ isOpen: false, order: null });
    const [notification, setNotification] = useState({ show: false, message: '', type: 'success' });
    
    useEffect(() => {
        fetchOrders();
    }, []);
    
    const fetchOrders = async () => {
        setLoading(true);
        try {
            const data = await api.getActiveOrders();
            setOrders(data as any[]);
        } catch (err) {
            setError('Failed to load active orders.');
        } finally {
            setLoading(false);
        }
    };
    
    const handleOpenModal = (order) => {
        setModalInfo({ isOpen: true, order: order });
    };

    const handleCloseModal = () => {
        setModalInfo({ isOpen: false, order: null });
    };

    const handleOrderUpdate = async (orderId, orderData) => {
        try {
            await api.updateOrder(orderId, orderData);
            setNotification({ show: true, message: `Order ${orderId} updated successfully!`, type: 'success' });
            // Refresh the list to show updated data
            const updatedOrders = orders.map(o => o.id === orderId ? { ...o, ...orderData } : o);
            setOrders(updatedOrders);
        } catch(err) {
            setNotification({ show: true, message: `Failed to update order: ${err.message}`, type: 'error' });
        }
    };
    
    const getStatusStyle = (status) => {
        const baseStyle = { ...styles.statusBadge };
        switch (status) {
            case 'Awaiting Production': return { ...baseStyle, color: '#FBBF24', backgroundColor: 'rgba(251, 191, 36, 0.1)', border: '1px solid rgba(251, 191, 36, 0.3)' };
            case 'In Production': return { ...baseStyle, color: '#60A5FA', backgroundColor: 'rgba(96, 165, 250, 0.1)', border: '1px solid rgba(96, 165, 250, 0.3)' };
            case 'Shipped': return { ...baseStyle, color: '#34D399', backgroundColor: 'rgba(52, 211, 153, 0.1)', border: '1px solid rgba(52, 211, 153, 0.3)' };
            case 'Delivered': return { ...baseStyle, color: '#86EFAC', backgroundColor: 'rgba(134, 239, 172, 0.1)', border: '1px solid rgba(134, 239, 172, 0.3)' };
            case 'Cancelled': return { ...baseStyle, color: '#F87171', backgroundColor: 'rgba(248, 113, 113, 0.1)', border: '1px solid rgba(248, 113, 113, 0.3)' };
            default: return { ...baseStyle, color: '#94A3B8', backgroundColor: 'rgba(148, 163, 184, 0.1)', border: '1px solid rgba(148, 163, 184, 0.2)' };
        }
    };

    if (loading) return <div>Loading orders...</div>;
    if (error) return <p style={styles.loginError}>{error}</p>;

    return (
        <div>
            <h2 style={styles.dashboardPageTitle}>Active Orders</h2>
            <p style={styles.dashboardPageSubtitle}>Manage orders that are in production or have been recently completed.</p>
            {notification.show && <Notification message={notification.message} type={notification.type} onDismiss={() => setNotification({ show: false, message: '', type: 'success' })} />}
            <div style={styles.tableContainer}>
                <table style={styles.table}>
                    <thead>
                        <tr>
                            <th style={styles.tableHeader}>Order ID</th>
                            <th style={styles.tableHeader}>Part Name</th>
                            <th style={styles.tableHeader}>Customer</th>
                            <th style={styles.tableHeader}>Date</th>
                            <th style={styles.tableHeader}>Status</th>
                            <th style={styles.tableHeader}>Tracking</th>
                            <th style={styles.tableHeader}>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {orders.length > 0 ? orders.map((order: any) => (
                            <tr key={order.id}>
                                <td style={styles.tableCell}>{order.id}</td>
                                <td style={styles.tableCell}>{order.designName}</td>
                                <td style={styles.tableCell}>{order.customer}</td>
                                <td style={styles.tableCell}>{new Date(order.dateCreated).toLocaleDateString()}</td>
                                <td style={styles.tableCell}><span style={getStatusStyle(order.status)}>{order.status}</span></td>
                                <td style={{...styles.tableCell, fontFamily: 'monospace'}}>{order.trackingNumber || 'N/A'}</td>
                                <td style={styles.tableCell}>
                                    <div style={{display: 'flex', gap: '8px', alignItems: 'center'}}>
                                        <CtaButton text="Manage" primary onClick={() => handleOpenModal(order)} className="button-small" />
                                        <CtaButton text="View Files" onClick={() => onViewFiles(order.designId)} className="button-small" />
                                    </div>
                                </td>
                            </tr>
                        )) : (
                            <tr><td colSpan={7} style={{...styles.tableCell, textAlign: 'center'}}>No active orders found.</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
            {modalInfo.isOpen && <UpdateOrderModal order={modalInfo.order} onClose={handleCloseModal} onUpdate={handleOrderUpdate} />}
        </div>
    );
};

const ManufacturerDashboard = ({ user, onViewFiles }) => {
    const [activeView, setActiveView] = useState('overview'); // overview, profile, quotes, orders
    const navItems = [
        { id: 'overview', label: 'Overview', icon: ChartPieIcon },
        { id: 'quotes', label: 'Quote Requests', icon: DocumentTextIcon },
        { id: 'orders', label: 'Active Orders', icon: CogIcon },
        { id: 'profile', label: 'Profile Management', icon: UserCircleIcon },
    ];
    
    const renderActiveView = () => {
        switch(activeView) {
            case 'profile': return <ManufacturerProfileManagementPage />;
            case 'quotes': return <QuoteRequestsPage onViewFiles={onViewFiles} />;
            case 'orders': return <ActiveOrdersPage onViewFiles={onViewFiles} />;
            case 'overview':
            default:
                return <DashboardOverview user={user} />;
        }
    };
    
    return (
        <div style={styles.dashboardContainer}>
            <aside style={styles.dashboardSidebar}>
                <h2 style={styles.dashboardSidebarTitle}>Manufacturer<br/>Dashboard</h2>
                <nav style={styles.dashboardNav}>
                    {navItems.map(item => {
                        const Icon = item.icon;
                        const isActive = activeView === item.id;
                        return (
                            <a 
                                key={item.id} 
                                href="#" 
                                onClick={(e) => { e.preventDefault(); setActiveView(item.id); }}
                                style={{...styles.dashboardNavLink, ...(isActive && styles.dashboardNavLinkActive)}}
                            >
                                <Icon style={{width: '20px', height: '20px', marginRight: '12px'}} />
                                {item.label}
                            </a>
                        );
                    })}
                </nav>
            </aside>
            <main style={styles.dashboardMainContent}>
                {renderActiveView()}
            </main>
        </div>
    );
};

// --- Customer Dashboard Components ---

const CustomerDashboardOverview = ({ user }) => (
    <div>
        <h2 style={styles.dashboardPageTitle}>Overview</h2>
        <p style={{ ...styles.stepText, fontSize: '18px' }}>Welcome back, {user?.company_name}!</p>
        <div style={styles.statsGrid}>
            <div style={styles.statCard}>
                <h3 style={styles.statValue}>4</h3>
                <p style={styles.statLabel}>Active Designs</p>
            </div>
            <div style={styles.statCard}>
                <h3 style={styles.statValue}>3</h3>
                <p style={styles.statLabel}>Open Orders</p>
            </div>
            <div style={styles.statCard}>
                <h3 style={styles.statValue}>$3,050.00</h3>
                <p style={styles.statLabel}>Total Spent</p>
            </div>
             <div style={styles.statCard}>
                <h3 style={styles.statValue}>1</h3>
                <p style={styles.statLabel}>New Quote Received</p>
            </div>
        </div>
    </div>
);

const CustomerProfilePage = () => {
    const [formData, setFormData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [notification, setNotification] = useState({ show: false, message: '', type: 'success' });
    
    useEffect(() => {
        const fetchProfile = async () => {
            setLoading(true);
            try {
                const profile = await api.getCustomerProfile();
                setFormData(profile);
            } catch (err) {
                setError('Failed to load profile data.');
            } finally {
                setLoading(false);
            }
        };
        fetchProfile();
    }, []);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };
    
    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setNotification({ show: false, message: '', type: 'success' });
        try {
            await api.updateCustomerProfile(formData);
            setNotification({ show: true, message: 'Profile updated successfully!', type: 'success' });
        } catch (err) {
            setNotification({ show: true, message: err.message, type: 'error' });
        } finally {
            setLoading(false);
        }
    };
    
    if (loading) return <div>Loading profile...</div>;
    if (error) return <p style={styles.loginError}>{error}</p>;
    if (!formData) return <p>Could not load profile data.</p>;
    
    return (
        <div>
            <h2 style={styles.dashboardPageTitle}>My Profile</h2>
            <p style={styles.dashboardPageSubtitle}>Update your company and contact information.</p>
            {notification.show && <Notification message={notification.message} type={notification.type} onDismiss={() => setNotification({ show: false, message: '', type: 'success' })} />}
            <form onSubmit={handleSubmit} style={{maxWidth: '600px'}}>
                 <fieldset style={{...styles.fieldset, marginTop: 0}}>
                    <legend style={styles.legend}>Profile Information</legend>
                    <div style={styles.formGroup}>
                        <label htmlFor="companyName" style={styles.label}>Company Name</label>
                        <input type="text" name="companyName" value={formData.companyName} onChange={handleInputChange} style={styles.input} required />
                    </div>
                     <div style={{...styles.formGroup, marginTop: '20px'}}>
                        <label htmlFor="email" style={styles.label}>Contact Email Address</label>
                        <input type="email" name="email" value={formData.email} onChange={handleInputChange} style={styles.input} required />
                    </div>
                </fieldset>
                <div style={{marginTop: '24px'}}>
                    <CtaButton text={loading ? "Saving..." : "Save Changes"} primary type="submit" disabled={loading}/>
                </div>
            </form>
        </div>
    );
};

const CustomerDesignsPage = ({ onViewFiles }) => {
    const [designs, setDesigns] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [notification, setNotification] = useState({ show: false, message: '', type: 'success' });
    
    useEffect(() => {
        fetchDesigns();
    }, []);
    
    const fetchDesigns = async () => {
        setLoading(true);
        try {
            const data = await api.getCustomerDesigns();
            setDesigns(data);
        } catch (err) {
            setError('Failed to load your designs.');
        } finally {
            setLoading(false);
        }
    };
    
    const handleDelete = async (design) => {
        if (window.confirm(`Are you sure you want to delete the design "${design.name}"?`)) {
            try {
                await api.deleteCustomerDesign(design.id);
                setNotification({ show: true, message: `Design "${design.name}" deleted successfully.`, type: 'success' });
                setDesigns(prev => prev.filter(d => d.id !== design.id));
            } catch(err) {
                setNotification({ show: true, message: `Error deleting design: ${err.message}`, type: 'error' });
            }
        }
    };

    const getStatusStyle = (status) => {
        const baseStyle = { ...styles.statusBadge };
        switch (status) {
            case 'Analysis Complete': return { ...baseStyle, color: '#34D399', backgroundColor: 'rgba(52, 211, 153, 0.1)', border: '1px solid rgba(52, 211, 153, 0.3)' };
            case 'Quoting': return { ...baseStyle, color: '#60A5FA', backgroundColor: 'rgba(96, 165, 250, 0.1)', border: '1px solid rgba(96, 165, 250, 0.3)' };
            case 'Ordered': return { ...baseStyle, color: '#86EFAC', backgroundColor: 'rgba(134, 239, 172, 0.1)', border: '1px solid rgba(134, 239, 172, 0.3)' };
            case 'Analysis Failed': return { ...baseStyle, color: '#F87171', backgroundColor: 'rgba(248, 113, 113, 0.1)', border: '1px solid rgba(248, 113, 113, 0.3)' };
            default: return { ...baseStyle, color: '#94A3B8', backgroundColor: 'rgba(148, 163, 184, 0.1)', border: '1px solid rgba(148, 163, 184, 0.2)' };
        }
    };

    if (loading) return <div>Loading designs...</div>;
    if (error) return <p style={styles.loginError}>{error}</p>;

    return (
        <div>
            <h2 style={styles.dashboardPageTitle}>My Designs</h2>
            <p style={styles.dashboardPageSubtitle}>Manage your uploaded designs and check their quoting status.</p>
            {notification.show && <Notification message={notification.message} type={notification.type} onDismiss={() => setNotification({ show: false, message: '', type: 'success' })} />}
            <div style={styles.tableContainer}>
                <table style={styles.table}>
                    <thead>
                        <tr>
                            <th style={styles.tableHeader}>Design Name</th>
                            <th style={styles.tableHeader}>Material</th>
                            <th style={styles.tableHeader}>Quantity</th>
                            <th style={styles.tableHeader}>Date Uploaded</th>
                            <th style={styles.tableHeader}>Status</th>
                            <th style={styles.tableHeader}>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {designs.length > 0 ? designs.map(design => (
                            <tr key={design.id}>
                                <td style={styles.tableCell}>{design.name}</td>
                                <td style={styles.tableCell}>{design.material}</td>
                                <td style={styles.tableCell}>{design.quantity}</td>
                                <td style={styles.tableCell}>{new Date(design.dateUploaded).toLocaleDateString()}</td>
                                <td style={styles.tableCell}><span style={getStatusStyle(design.status)}>{design.status}</span></td>
                                <td style={styles.tableCell}>
                                    <div style={{display: 'flex', gap: '8px'}}>
                                        <CtaButton text="View Files" onClick={() => onViewFiles(design.id)} className="button-small" />
                                        <CtaButton text="Delete" onClick={() => handleDelete(design)} className="button-small-danger" />
                                    </div>
                                </td>
                            </tr>
                        )) : (
                             <tr><td colSpan={6} style={{...styles.tableCell, textAlign: 'center'}}>You haven't uploaded any designs yet.</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

const CustomerOrdersPage = ({ onViewFiles }) => {
    const [orders, setOrders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    
    useEffect(() => {
        const fetchOrders = async () => {
            setLoading(true);
            try {
                const data = await api.getCustomerOrders();
                setOrders(data);
            } catch (err) {
                setError('Failed to load your orders.');
            } finally {
                setLoading(false);
            }
        };
        fetchOrders();
    }, []);

    const getStatusStyle = (status) => {
        const baseStyle = { ...styles.statusBadge };
        switch (status) {
            case 'Awaiting Production': return { ...baseStyle, color: '#FBBF24', backgroundColor: 'rgba(251, 191, 36, 0.1)', border: '1px solid rgba(251, 191, 36, 0.3)' };
            case 'In Production': return { ...baseStyle, color: '#60A5FA', backgroundColor: 'rgba(96, 165, 250, 0.1)', border: '1px solid rgba(96, 165, 250, 0.3)' };
            case 'Shipped': return { ...baseStyle, color: '#34D399', backgroundColor: 'rgba(52, 211, 153, 0.1)', border: '1px solid rgba(52, 211, 153, 0.3)' };
            case 'Delivered': return { ...baseStyle, color: '#86EFAC', backgroundColor: 'rgba(134, 239, 172, 0.1)', border: '1px solid rgba(134, 239, 172, 0.3)' };
            case 'Cancelled': return { ...baseStyle, color: '#F87171', backgroundColor: 'rgba(248, 113, 113, 0.1)', border: '1px solid rgba(248, 113, 113, 0.3)' };
            default: return { ...baseStyle, color: '#94A3B8', backgroundColor: 'rgba(148, 163, 184, 0.1)', border: '1px solid rgba(148, 163, 184, 0.2)' };
        }
    };

    if (loading) return <div>Loading orders...</div>;
    if (error) return <p style={styles.loginError}>{error}</p>;

    return (
        <div>
            <h2 style={styles.dashboardPageTitle}>My Orders</h2>
            <p style={styles.dashboardPageSubtitle}>Track your active and completed orders.</p>
            <div style={styles.tableContainer}>
                <table style={styles.table}>
                    <thead>
                        <tr>
                            <th style={styles.tableHeader}>Order ID</th>
                            <th style={styles.tableHeader}>Design Name</th>
                            <th style={styles.tableHeader}>Manufacturer</th>
                            <th style={styles.tableHeader}>Price</th>
                            <th style={styles.tableHeader}>Status</th>
                            <th style={styles.tableHeader}>Tracking</th>
                             <th style={styles.tableHeader}>Files</th>
                        </tr>
                    </thead>
                    <tbody>
                        {orders.length > 0 ? orders.map(order => (
                            <tr key={order.id}>
                                <td style={{...styles.tableCell, fontFamily: 'monospace'}}>{order.id}</td>
                                <td style={styles.tableCell}>{order.designName}</td>
                                <td style={styles.tableCell}>{order.manufacturer}</td>
                                <td style={styles.tableCell}>${order.price.toFixed(2)}</td>
                                <td style={styles.tableCell}><span style={getStatusStyle(order.status)}>{order.status}</span></td>
                                <td style={{...styles.tableCell, fontFamily: 'monospace'}}>
                                    {order.trackingNumber ? (
                                        <a href={`https://www.google.com/search?q=${order.trackingNumber}`} target="_blank" rel="noopener noreferrer" style={styles.loginLink}>
                                            {order.trackingNumber} ({order.shippingCarrier})
                                        </a>
                                    ) : 'N/A'}
                                </td>
                                <td style={styles.tableCell}>
                                     <CtaButton text="View Files" onClick={() => onViewFiles(order.designId)} className="button-small" />
                                </td>
                            </tr>
                        )) : (
                            <tr><td colSpan={7} style={{...styles.tableCell, textAlign: 'center'}}>You have no orders.</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};


const CustomerDashboard = ({ user, onViewFiles }) => {
    const [activeView, setActiveView] = useState('overview');
    const navItems = [
        { id: 'overview', label: 'Overview', icon: ChartPieIcon },
        { id: 'designs', label: 'My Designs', icon: CubeIcon },
        { id: 'orders', label: 'My Orders', icon: ArchiveBoxIcon },
        { id: 'profile', label: 'Profile', icon: UserCircleIcon },
    ];
    
    const renderActiveView = () => {
        switch(activeView) {
            case 'designs': return <CustomerDesignsPage onViewFiles={onViewFiles} />;
            case 'orders': return <CustomerOrdersPage onViewFiles={onViewFiles} />;
            case 'profile': return <CustomerProfilePage />;
            case 'overview':
            default:
                return <CustomerDashboardOverview user={user} />;
        }
    };
    
    return (
        <div style={styles.dashboardContainer}>
            <aside style={styles.dashboardSidebar}>
                <h2 style={styles.dashboardSidebarTitle}>Customer<br/>Dashboard</h2>
                <nav style={styles.dashboardNav}>
                    {navItems.map(item => {
                        const Icon = item.icon;
                        const isActive = activeView === item.id;
                        return (
                            <a 
                                key={item.id} 
                                href="#" 
                                onClick={(e) => { e.preventDefault(); setActiveView(item.id); }}
                                style={{...styles.dashboardNavLink, ...(isActive && styles.dashboardNavLinkActive)}}
                            >
                                <Icon style={{width: '20px', height: '20px', marginRight: '12px'}} />
                                {item.label}
                            </a>
                        );
                    })}
                </nav>
            </aside>
            <main style={styles.dashboardMainContent}>
                {renderActiveView()}
            </main>
        </div>
    );
};


// --- Styles ---
const neon_cyan = '#0AF0F0';
const neon_magenta = '#F005B4';
const neon_orange = '#FF7A00';
const bg_deep_space = '#02040a';
const text_primary = '#E0E7FF';
const text_secondary = '#94A3B8';
const border_color = 'rgba(175, 200, 255, 0.15)';
const border_color_strong = 'rgba(175, 200, 255, 0.3)';

// --- Background Animation ---

const backgroundParts = [
    { id: 1, initialTop: '50%', initialLeft: '50%', initialRotate: {x: 20, y: -30, z: 45}, size: 250, depth: -300, style: { border: `3px solid ${neon_cyan}`, borderRadius: '50%', opacity: 0.2, filter: `drop-shadow(0 0 8px ${neon_cyan})` }, factors: { y: -0.4, x: 0.3, rotateX: 0.01, rotateY: 0.02, rotateZ: 0.05 } },
    { id: 2, initialTop: '40%', initialLeft: '60%', initialRotate: {x: 0, y: 0, z: 10}, size: 150, depth: 200, style: { borderTop: `2px solid ${neon_magenta}`, borderBottom: `2px solid ${neon_magenta}`, borderLeft: `2px solid ${neon_magenta}`, opacity: 0.3, filter: `drop-shadow(0 0 8px ${neon_magenta})` }, factors: { y: 0.2, x: -0.5, rotateX: -0.02, rotateY: -0.01, rotateZ: -0.08 } },
    { id: 3, initialTop: '20%', initialLeft: '30%', initialRotate: {x: 45, y: 45, z: 0}, size: 80, depth: -100, style: { border: `2px solid ${neon_orange}`, opacity: 0.25, filter: `drop-shadow(0 0 6px ${neon_orange})` }, factors: { y: 0.6, x: 0.2, rotateX: 0.05, rotateY: 0.05, rotateZ: 0.1 } },
    { id: 4, initialTop: '80%', initialLeft: '25%', initialRotate: {x: -20, y: 0, z: 0}, size: 180, depth: 300, style: { borderRight: `2px solid ${neon_cyan}`, borderLeft: `2px solid ${neon_cyan}`, opacity: 0.2, filter: `drop-shadow(0 0 8px ${neon_cyan})` }, factors: { y: -0.2, x: 0.6, rotateX: 0.03, rotateY: -0.04, rotateZ: -0.03 } },
    { id: 5, initialTop: '15%', initialLeft: '75%', initialRotate: {x: 0, y: 60, z: -30}, size: 100, depth: 50, style: { border: `3px solid ${neon_magenta}`, borderRadius: '50%', borderStyle: 'dashed', opacity: 0.3, filter: `drop-shadow(0 0 8px ${neon_magenta})` }, factors: { y: 0.5, x: -0.3, rotateX: -0.01, rotateY: -0.05, rotateZ: 0.15 } },
    { id: 6, initialTop: '75%', initialLeft: '65%', initialRotate: {x: -60, y: 0, z: 120}, size: 60, depth: -250, style: { border: `4px solid ${neon_cyan}`, opacity: 0.35, filter: `drop-shadow(0 0 8px ${neon_cyan})` }, factors: { y: -0.6, x: -0.4, rotateX: 0.1, rotateY: -0.1, rotateZ: 0.2 } },
];

const BackgroundAnimation = () => {
    const [scrollY, setScrollY] = useState(0);
    const [mousePos, setMousePos] = useState({ x: window.innerWidth / 2, y: window.innerHeight / 2 });
    const [dimensions, setDimensions] = useState({ width: window.innerWidth, height: window.innerHeight });
    const animationFrameId = useRef<number | null>(null);

    useEffect(() => {
        let scrollTicking = false;
        const handleScroll = () => {
            if (!scrollTicking) {
                window.requestAnimationFrame(() => {
                    setScrollY(window.scrollY);
                    scrollTicking = false;
                });
                scrollTicking = true;
            }
        };

        const handleMouseMove = (e: MouseEvent) => {
            if (animationFrameId.current) {
                cancelAnimationFrame(animationFrameId.current);
            }
            animationFrameId.current = requestAnimationFrame(() => {
                setMousePos({ x: e.clientX, y: e.clientY });
            });
        };
        
        let resizeTicking = false;
        const handleResize = () => {
            if (!resizeTicking) {
                window.requestAnimationFrame(() => {
                    setDimensions({ width: window.innerWidth, height: window.innerHeight });
                    resizeTicking = false;
                });
                resizeTicking = true;
            }
        };

        window.addEventListener('scroll', handleScroll, { passive: true });
        window.addEventListener('mousemove', handleMouseMove);
        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('scroll', handleScroll);
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('resize', handleResize);
            if (animationFrameId.current) {
                cancelAnimationFrame(animationFrameId.current);
            }
        };
    }, []);

    return (
        <div style={styles.backgroundAnimationContainer}>
            {backgroundParts.map(part => {
                const scrollTranslateX = part.factors.x * scrollY;
                const scrollTranslateY = part.factors.y * scrollY;

                // Mouse interaction
                const partCenterX = (parseFloat(part.initialLeft) / 100) * dimensions.width + scrollTranslateX;
                const partCenterY = (parseFloat(part.initialTop) / 100) * dimensions.height + scrollTranslateY;
                const dx = partCenterX - mousePos.x;
                const dy = partCenterY - mousePos.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                const interactionRadius = 250;
                const maxPush = 30;

                let mousePushX = 0;
                let mousePushY = 0;

                if (distance < interactionRadius) {
                    const force = 1 - (distance / interactionRadius);
                    const pushAmount = force * maxPush;
                    const angle = Math.atan2(dy, dx);
                    mousePushX = Math.cos(angle) * pushAmount;
                    mousePushY = Math.sin(angle) * pushAmount;
                }

                const transform = `
                    translate3d(-50%, -50%, 0)
                    translateX(${scrollTranslateX + mousePushX}px)
                    translateY(${scrollTranslateY + mousePushY}px)
                    translateZ(${part.depth}px)
                    rotateX(${part.initialRotate.x + part.factors.rotateX * scrollY}deg)
                    rotateY(${part.initialRotate.y + part.factors.rotateY * scrollY}deg)
                    rotateZ(${part.initialRotate.z + part.factors.rotateZ * scrollY}deg)
                `;

                const opacity = Math.max(0, (part.style.opacity || 1) - (scrollY / 2000));

                return (
                    <div
                        key={part.id}
                        style={{
                            ...styles.animatedPart,
                            ...part.style,
                            width: `${part.size}px`,
                            height: `${part.size}px`,
                            top: part.initialTop,
                            left: part.initialLeft,
                            transform: transform,
                            opacity: opacity,
                        }}
                    />
                );
            })}
        </div>
    );
};


// --- Main App Component ---

const App = () => {
    const [page, setPage] = useState('landing');
    const [pageParams, setPageParams] = useState(null);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [user, setUser] = useState(null);
    const [loginReasonMessage, setLoginReasonMessage] = useState('');
    const [pendingUploadData, setPendingUploadData] = useState(null);
    const [fileViewerState, setFileViewerState] = useState({ isOpen: false, design: null });

    useEffect(() => {
        const checkAuth = async () => {
            const { access } = getTokens();
            if (access) {
                try {
                    // This is a mock API call for demonstration.
                    // In a real app, `api.getMe()` would be used.
                    const storedRole = localStorage.getItem('userRole'); // Simple role persistence
                    const storedCompanyName = localStorage.getItem('userCompanyName');
                    if (storedRole) {
                         setUser({ role: storedRole, company_name: storedCompanyName });
                         setIsAuthenticated(true);
                    } else {
                        // Fallback if role isn't stored, clear tokens
                         clearTokens();
                    }
                } catch (error) {
                    console.error("Auth check failed", error);
                    clearTokens();
                    setIsAuthenticated(false);
                    setUser(null);
                }
            }
        };
        checkAuth();
    }, []);

    const handleNavigate = (newPage, params = null) => {
        setPage(newPage);
        setPageParams(params);
        window.scrollTo(0, 0);
    };

    const handleLogin = async (credentials: { email: string }, role: string) => {
        try {
            const { access, refresh } = await new Promise<{access: string, refresh: string}>(res => setTimeout(() => res({access: 'mock-access-token', refresh: 'mock-refresh-token'}), 200));
            setTokens(access, refresh);
            const userData = { email: credentials.email, role: role, company_name: role === 'manufacturer' ? 'Precision Parts Co.' : 'Innovate Robotics' };
            setUser(userData as any);
            setIsAuthenticated(true);
            
            // Simple persistence for demo purposes
            localStorage.setItem('userRole', role);
            localStorage.setItem('userCompanyName', userData.company_name);

            if (pendingUploadData) {
                console.log("User logged in, proceeding with upload for:", (pendingUploadData as any).designName);
                console.log("Full upload data:", pendingUploadData);
                setPendingUploadData(null); // clear after use
                handleNavigate('dashboard');
                // In a real app, you would now trigger the actual upload and design creation
            } else {
                handleNavigate('dashboard');
            }
        } catch (error) {
            console.error("Login failed", error);
            throw error;
        }
    };
    
    const handleLogout = () => {
        clearTokens();
        localStorage.removeItem('userRole');
        localStorage.removeItem('userCompanyName');
        setIsAuthenticated(false);
        setUser(null);
        handleNavigate('landing');
    };
    
    const handleProceedToLogin = (uploadData) => {
        setPendingUploadData(uploadData);
        setLoginReasonMessage('Please log in or create an account to upload your design.');
        handleNavigate('login');
    };

    const handleViewFiles = async (designId) => {
        try {
            const design = await api.getDesignById(designId);
            if(design && design.files) {
                setFileViewerState({ isOpen: true, design: design });
            } else {
                alert("No files found for this design.");
            }
        } catch(err) {
            alert("Could not load files for this design.");
        }
    };

    const handleCloseFileViewer = () => {
        setFileViewerState({ isOpen: false, design: null });
    };

    const renderPage = () => {
        switch (page) {
            case 'landing': return <LandingPageContent onNavigate={handleNavigate} />;
            case 'how-it-works-detailed': return <PlaceholderPage title="How It Works" subtitle="A detailed breakdown of our simple, three-step process." />;
            case 'directory': return <ManufacturerDirectoryPage onNavigate={handleNavigate} />;
            case 'manufacturer-profile': return <ManufacturerProfilePage manufacturerId={pageParams} onNavigate={handleNavigate} />;
            case 'trust-and-security': return <TrustAndSecurityPage />;
            case 'about': return <PlaceholderPage title="About Us" subtitle="Learn more about our mission to revolutionize manufacturing." />;
            case 'blog': return <PlaceholderPage title="Blog" subtitle="Insights and articles from the manufacturing world." />;
            case 'contact': return <PlaceholderPage title="Contact Us" subtitle="Get in touch with the GMQP team." />;
            case 'faq': return <PlaceholderPage title="Frequently Asked Questions" subtitle="Find answers to common questions." />;
            case 'privacy': return <PlaceholderPage title="Privacy Policy" subtitle="How we handle your data." />;
            case 'terms': return <PlaceholderPage title="Terms of Service" subtitle="The rules of our platform." />;
            case 'login': return <LoginRoleSelector onNavigate={handleNavigate} reasonMessage={loginReasonMessage} />;
            case 'login-customer': return <LoginPage onLogin={handleLogin} onNavigate={handleNavigate} role="customer" />;
            case 'login-manufacturer': return <LoginPage onLogin={handleLogin} onNavigate={handleNavigate} role="manufacturer" />;
            case 'signup': return <SignupRoleSelector onNavigate={handleNavigate} />;
            case 'signup-customer': return <CustomerSignupPage onLogin={handleLogin} onNavigate={handleNavigate} />;
            case 'signup-manufacturer': return <ManufacturerSignupPage onLogin={handleLogin} onNavigate={handleNavigate} />;
            case 'upload': return <UploadPage onProceedToLogin={handleProceedToLogin} onNavigate={handleNavigate} />;
            case 'dashboard':
                if (!isAuthenticated) return <LoginRoleSelector onNavigate={handleNavigate} />;
                if (user?.role === 'manufacturer') {
                    return <ManufacturerDashboard user={user} onViewFiles={handleViewFiles} />;
                }
                if (user?.role === 'customer') {
                    return <CustomerDashboard user={user} onViewFiles={handleViewFiles} />;
                }
                // Fallback while user data is loading or if role is unknown
                return <div style={{...styles.container, padding: '64px 24px', textAlign: 'center'}}>Loading dashboard...</div>;
            default: return <LandingPageContent onNavigate={handleNavigate} />;
        }
    };

    return (
        <div style={{ backgroundColor: bg_deep_space }}>
            <BackgroundAnimation />
            <div style={{ ...styles.appWrapper, backgroundColor: 'transparent', position: 'relative', zIndex: 1 }}>
                <Header isAuthenticated={isAuthenticated} onLogout={handleLogout} onNavigate={handleNavigate} />
                <main style={styles.mainContent}>
                    {renderPage()}
                </main>
                {fileViewerState.isOpen && <FileViewerModal design={fileViewerState.design} onClose={handleCloseFileViewer} />}
                <Footer onNavigate={handleNavigate} />
            </div>
        </div>
    );
};

const styles: { [key: string]: React.CSSProperties } = {
    appWrapper: { 
        display: 'flex', 
        flexDirection: 'column', 
        minHeight: '100vh', 
        backgroundColor: bg_deep_space,
        color: text_primary,
        backgroundImage: `
            linear-gradient(rgba(175, 200, 255, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(175, 200, 255, 0.03) 1px, transparent 1px)
        `,
        backgroundSize: '30px 30px',
    },
    backgroundAnimationContainer: {
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        zIndex: 0,
        overflow: 'hidden',
        pointerEvents: 'none',
        perspective: '1000px',
        transformStyle: 'preserve-3d',
    },
    animatedPart: {
        position: 'absolute',
        willChange: 'transform, opacity',
        transition: 'transform 0.2s linear, opacity 0.2s linear',
        transformStyle: 'preserve-3d',
    },
    mainContent: { flex: 1, display: 'flex', flexDirection: 'column' },
    container: { width: '100%', maxWidth: '1200px', margin: '0 auto', padding: '0 24px', boxSizing: 'border-box' },
    header: { 
        backgroundColor: 'rgba(2, 4, 10, 0.7)', 
        backdropFilter: 'blur(12px)', 
        borderBottom: `1px solid ${border_color}`, 
        position: 'sticky', 
        top: 0, 
        zIndex: 50 
    },
    headerContent: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', height: '72px' },
    logo: { 
        fontWeight: 'bold', 
        fontSize: '24px', 
        color: text_primary, 
        textDecoration: 'none',
        textShadow: `0 0 4px ${neon_cyan}`
    },
    nav: { display: 'flex', gap: '32px' },
    navLink: { 
        color: text_secondary, 
        textDecoration: 'none', 
        fontWeight: 500, 
        fontSize: '15px', 
        transition: 'color 0.3s, text-shadow 0.3s' 
    },
    navLinkHover: { 
        color: neon_cyan,
        textShadow: `0 0 8px ${neon_cyan}`
    },
    headerActions: { display: 'flex', alignItems: 'center', gap: '16px' },
    button: { 
        display: 'inline-flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        padding: '10px 20px', 
        borderRadius: '8px', 
        border: '1px solid transparent', 
        fontWeight: 600, 
        fontSize: '15px', 
        textDecoration: 'none', 
        cursor: 'pointer', 
        transition: 'all 0.3s ease-in-out', 
        width: 'auto'
    },
    buttonPrimary: { 
        backgroundColor: 'rgba(10, 240, 240, 0.1)',
        color: neon_cyan,
        border: `1px solid ${neon_cyan}`,
        boxShadow: `0 0 5px rgba(10, 240, 240, 0.5), inset 0 0 5px rgba(10, 240, 240, 0.3)`,
        textShadow: `0 0 3px ${neon_cyan}`
    },
    buttonPrimaryHover: { 
        backgroundColor: 'rgba(10, 240, 240, 0.2)',
        boxShadow: `0 0 15px rgba(10, 240, 240, 0.8), inset 0 0 8px rgba(10, 240, 240, 0.5)`,
        transform: 'scale(1.02)'
    },
    buttonSecondary: { 
        backgroundColor: 'transparent', 
        color: neon_magenta, 
        border: `1px solid ${neon_magenta}`,
        boxShadow: `0 0 5px rgba(240, 5, 180, 0.4), inset 0 0 5px rgba(240, 5, 180, 0.2)`,
        textShadow: `0 0 3px ${neon_magenta}`
    },
    buttonSecondaryHover: { 
        backgroundColor: 'rgba(240, 5, 180, 0.15)',
        boxShadow: `0 0 15px rgba(240, 5, 180, 0.7), inset 0 0 8px rgba(240, 5, 180, 0.4)`,
        transform: 'scale(1.02)'
    },
    buttonDanger: {
        backgroundColor: 'transparent',
        color: neon_orange,
        border: `1px solid ${neon_orange}`,
        boxShadow: `0 0 5px rgba(255, 122, 0, 0.4), inset 0 0 5px rgba(255, 122, 0, 0.2)`,
        textShadow: `0 0 3px ${neon_orange}`
    },
    buttonDangerHover: {
        backgroundColor: `rgba(255, 122, 0, 0.15)`,
        boxShadow: `0 0 15px rgba(255, 122, 0, 0.7), inset 0 0 8px rgba(255, 122, 0, 0.4)`
    },
    buttonDisabled: { 
        backgroundColor: 'rgba(148, 163, 184, 0.1)', 
        color: 'rgba(148, 163, 184, 0.4)', 
        border: `1px solid rgba(148, 163, 184, 0.2)`,
        cursor: 'not-allowed', 
        boxShadow: 'none',
        textShadow: 'none',
        transform: 'none'
    },
    hero: { padding: '96px 0', textAlign: 'center' },
    heroContent: { maxWidth: '800px', margin: '0 auto' },
    heroTitle: { 
        fontSize: '56px', 
        fontWeight: 800, 
        color: text_primary, 
        lineHeight: 1.2, 
        letterSpacing: '-0.025em', 
        margin: '0 0 24px 0',
        textShadow: `0 0 5px ${neon_cyan}, 0 0 15px ${neon_cyan}, 0 0 30px rgba(10, 240, 240, 0.5)`
    },
    heroSubtitle: { 
        fontSize: '20px', 
        color: text_secondary, 
        lineHeight: 1.6, 
        maxWidth: '650px', 
        margin: '0 auto 32px auto',
        textShadow: `0 0 2px rgba(224, 231, 255, 0.3)`
    },
    heroActions: { display: 'flex', justifyContent: 'center', gap: '16px' },
    howItWorks: { padding: '96px 0' },
    sectionTitle: { 
        fontSize: '42px', 
        fontWeight: 700, 
        color: text_primary, 
        textAlign: 'center', 
        margin: '0 0 64px 0',
        textShadow: `0 0 8px ${neon_magenta}`
    },
    stepsGrid: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '48px', textAlign: 'center' },
    step: {},
    stepTitle: { 
        fontSize: '20px', 
        fontWeight: 600, 
        color: text_primary, 
        margin: '16px 0 8px 0',
        textShadow: `0 0 4px ${text_primary}`
    },
    stepText: { color: text_secondary, lineHeight: 1.6, margin: 0 },
    features: { padding: '96px 0', backgroundColor: 'rgba(2, 4, 10, 0.5)' },
    valueGrid: { display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '32px' },
    valueCard: { 
        backgroundColor: 'rgba(16, 24, 48, 0.4)',
        padding: '32px', 
        borderRadius: '12px', 
        textAlign: 'center', 
        border: `1px solid ${border_color}`, 
        transition: 'transform 0.3s, box-shadow 0.3s, border-color 0.3s',
        boxShadow: 'inset 0 0 10px rgba(10, 240, 240, 0.1)'
    },
    valueCardHover: { 
        transform: 'translateY(-8px) scale(1.03)', 
        borderColor: neon_cyan,
        boxShadow: `0 0 20px rgba(10, 240, 240, 0.5), inset 0 0 15px rgba(10, 240, 240, 0.3)`
    },
    forWhomGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px' },
    forWhomCard: { 
        backgroundColor: 'rgba(16, 24, 48, 0.6)', 
        padding: '40px', 
        borderRadius: '12px', 
        border: `1px solid ${border_color_strong}`,
        display: 'flex',
        flexDirection: 'column'
    },
    forWhomIcon: {
        width: '32px',
        height: '32px',
        marginBottom: 0,
        filter: 'drop-shadow(0 0 8px currentColor)'
    },
    featureTitle: { 
        fontSize: '24px', 
        fontWeight: 600, 
        color: text_primary, 
        margin: 0,
        textShadow: `0 0 5px currentColor`
    },
    forWhomText: { color: text_secondary, lineHeight: 1.6, margin: '16px 0 24px 0', flexGrow: 1 },
    featureList: { 
        listStyle: 'none', 
        padding: 0, 
        margin: '0 0 32px 0', 
        display: 'flex', 
        flexDirection: 'column', 
        gap: '12px', 
        color: text_secondary,
    },
    socialProofGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px' },
    testimonialCard: { backgroundColor: 'rgba(16, 24, 48, 0.4)', padding: '32px', borderRadius: '12px', border: `1px solid ${border_color}` },
    testimonialText: { fontStyle: 'italic', color: text_primary, lineHeight: 1.6, margin: '0 0 16px 0' },
    testimonialAuthor: { fontWeight: 600, color: neon_magenta, textShadow: `0 0 5px ${neon_magenta}` },
    metricsContainer: { display: 'flex', justifyContent: 'space-around', marginTop: '80px', borderTop: `1px solid ${border_color}`, paddingTop: '64px' },
    metricItem: { textAlign: 'center' },
    metricValue: { display: 'block', fontSize: '42px', fontWeight: 700, color: neon_cyan, textShadow: `0 0 10px ${neon_cyan}` },
    metricLabel: { color: text_secondary, marginTop: '8px' },
    footer: { backgroundColor: 'rgba(2, 4, 10, 0.8)', color: text_secondary, padding: '64px 0', borderTop: `1px solid ${border_color}` },
    footerGrid: { display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '32px', paddingBottom: '48px' },
    footerColumn: { display: 'flex', flexDirection: 'column', gap: '12px' },
    footerHeading: { color: text_primary, fontWeight: 600, fontSize: '16px', margin: '0 0 8px 0' },
    footerLink: { color: text_secondary, textDecoration: 'none', transition: 'color 0.2s, text-shadow 0.2s' },
    footerBottom: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: `1px solid ${border_color_strong}`, paddingTop: '32px', marginTop: '32px' },
    footerCopyright: { fontSize: '14px' },
    footerSocials: { display: 'flex', gap: '16px' },
    footerSocialLink: { color: text_secondary, textDecoration: 'none', transition: 'color 0.2s, filter 0.2s', filter: 'grayscale(50%)' },
    featureCard: { backgroundColor: 'rgba(16, 24, 48, 0.6)', padding: '32px', borderRadius: '12px', border: `1px solid ${border_color}` },
    loginPage: { flexGrow: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '64px 24px' },
    loginContainer: { 
        width: '100%', 
        maxWidth: '450px', 
        backgroundColor: 'rgba(2, 4, 10, 0.8)', 
        backdropFilter: 'blur(10px)',
        padding: '48px', 
        borderRadius: '12px', 
        boxShadow: `0 0 30px rgba(10, 240, 240, 0.3), inset 0 0 10px rgba(240, 5, 180, 0.2)`, 
        border: `1px solid ${neon_cyan}` 
    },
    loginTitle: { fontSize: '32px', fontWeight: 700, color: text_primary, textAlign: 'center', margin: '0 0 12px 0', textShadow: `0 0 5px ${neon_cyan}` },
    loginSubtitle: { fontSize: '16px', color: text_secondary, textAlign: 'center', margin: '0 0 32px 0' },
    loginForm: { display: 'flex', flexDirection: 'column', gap: '20px' },
    loginError: { color: '#F87171', backgroundColor: 'rgba(248, 113, 113, 0.1)', padding: '12px', borderRadius: '8px', border: '1px solid #F87171', textAlign: 'center', fontSize: '14px', textShadow: '0 0 5px #F87171' },
    loginReasonMessage: { color: '#60A5FA', backgroundColor: 'rgba(96, 165, 250, 0.1)', padding: '12px', borderRadius: '8px', border: '1px solid #60A5FA', textAlign: 'center', fontSize: '14px', marginBottom: '24px' },
    formGroup: { display: 'flex', flexDirection: 'column' },
    label: { fontWeight: 500, color: text_secondary, marginBottom: '8px', fontSize: '14px' },
    input: { 
        padding: '10px 12px', 
        borderRadius: '8px', 
        border: `1px solid ${border_color_strong}`, 
        fontSize: '16px', 
        transition: 'border-color 0.2s, box-shadow 0.2s', 
        backgroundColor: 'rgba(0,0,0,0.3)', 
        color: text_primary,
        width: '100%', 
        boxSizing: 'border-box' 
    },
    loginLinks: { display: 'flex', justifyContent: 'space-between', marginTop: '24px', fontSize: '14px' },
    loginLink: { color: neon_cyan, textDecoration: 'none', transition: 'filter 0.2s', filter: 'brightness(0.9)' },
    fieldset: { border: `1px solid ${border_color}`, borderRadius: '8px', padding: '24px', margin: '24px 0 0 0', backgroundColor: 'rgba(16, 24, 48, 0.4)' },
    legend: { fontWeight: 600, fontSize: '18px', color: neon_magenta, padding: '0 8px', textShadow: `0 0 5px ${neon_magenta}` },
    fieldsetDescription: { color: text_secondary, fontSize: '14px', marginTop: '-8px', marginBottom: '16px' },
    subLegend: { fontWeight: 600, color: text_primary, marginBottom: '12px', fontSize: '16px' },
    formRow: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' },
    checkboxGrid: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px 24px' },
    checkboxLabel: { display: 'flex', alignItems: 'center', fontSize: '14px', color: text_secondary, cursor: 'pointer' },
    checkboxInput: { marginRight: '8px', width: '16px', height: '16px', accentColor: neon_cyan, backgroundColor: 'rgba(0,0,0,0.3)', border: `1px solid ${border_color_strong}` },
    uploadPageContainer: { width: '100%', maxWidth: '1200px', margin: '0 auto', padding: '64px 24px', boxSizing: 'border-box', flexGrow: 1 },
    dashboardHeader: { borderBottom: `1px solid ${border_color}`, paddingBottom: '16px', marginBottom: '24px' },
    dashboardTitle: { fontSize: '36px', fontWeight: 700, color: text_primary, margin: 0, textShadow: `0 0 8px ${neon_cyan}` },
    uploadLayout: { display: 'grid', gridTemplateColumns: '1fr 1.2fr', gap: '48px', marginTop: '24px' },
    uploadDropzoneWrapper: {},
    uploadDropzone: { border: `2px dashed ${border_color_strong}`, borderRadius: '12px', padding: '48px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', cursor: 'pointer', transition: 'all 0.3s', backgroundColor: 'rgba(16, 24, 48, 0.4)' },
    uploadDropzoneActive: { borderColor: neon_cyan, backgroundColor: 'rgba(10, 240, 240, 0.1)', boxShadow: `0 0 15px rgba(10, 240, 240, 0.3)` },
    uploadFileInfo: { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', color: neon_cyan },
    uploadFileName: { fontWeight: 500, color: text_primary },
    uploadFormFields: { display: 'flex', flexDirection: 'column', gap: '20px' },
    supportingFileList: { marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '8px' },
    supportingFileItem: { display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 12px', backgroundColor: 'rgba(0,0,0,0.3)', borderRadius: '6px', border: `1px solid ${border_color}` },
    supportingFileName: { flexGrow: 1, fontSize: '14px', color: text_secondary, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' },
    supportingFileRemoveBtn: { background: 'none', border: 'none', cursor: 'pointer', color: text_secondary, padding: '4px', display: 'flex', alignItems: 'center', borderRadius: '50%' },
    directoryLayout: { display: 'grid', gridTemplateColumns: '280px 1fr', gap: '48px', marginTop: '48px' },
    directoryFilters: { backgroundColor: 'rgba(16, 24, 48, 0.4)', padding: '24px', borderRadius: '12px', border: `1px solid ${border_color}` },
    directoryResults: {},
    searchContainer: { position: 'relative', marginTop: '24px' },
    searchInput: { padding: '10px 12px', paddingLeft: '40px', borderRadius: '8px', border: `1px solid ${border_color_strong}`, fontSize: '16px', transition: 'border-color 0.2s, box-shadow 0.2s', width: '100%', boxSizing: 'border-box', backgroundColor: 'rgba(0,0,0,0.3)', color: text_primary },
    mfgGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '24px' },
    mfgCard: { backgroundColor: 'rgba(16, 24, 48, 0.6)', padding: '24px', borderRadius: '12px', border: `1px solid ${border_color}`, transition: 'transform 0.3s, box-shadow 0.3s, border-color 0.3s', cursor: 'pointer' },
    mfgCardHover: { transform: 'translateY(-5px) scale(1.02)', boxShadow: `0 0 25px rgba(240, 5, 180, 0.4)`, borderColor: neon_magenta },
    mfgCardLogo: { width: '50px', height: '50px', borderRadius: '50%', objectFit: 'cover', border: `2px solid ${border_color_strong}`, backgroundColor: bg_deep_space, flexShrink: 0 },
    mfgCardTitle: { fontSize: '18px', fontWeight: '600', color: text_primary, margin: '0 0 4px 0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
    mfgCardLocation: { fontSize: '14px', color: text_secondary, margin: '0', display: 'flex', alignItems: 'center' },
    mfgCardSectionTitle: { fontSize: '12px', fontWeight: '600', color: text_secondary, textTransform: 'uppercase', letterSpacing: '0.05em', margin: '0 0 8px 0' },
    mfgCardTagContainer: { display: 'flex', flexWrap: 'wrap', gap: '6px' },
    mfgCardTag: { backgroundColor: 'rgba(10, 240, 240, 0.1)', color: neon_cyan, padding: '4px 8px', borderRadius: '6px', fontSize: '12px', fontWeight: 500 },
    mfgCardCertTag: { backgroundColor: 'rgba(52, 211, 153, 0.1)', color: '#34D399', padding: '4px 8px', borderRadius: '6px', fontSize: '12px', fontWeight: 500 },
    mfgCardMaterialTag: { backgroundColor: 'rgba(148, 163, 184, 0.1)', color: text_secondary, padding: '4px 8px', borderRadius: '6px', fontSize: '12px', fontWeight: 500 },
    mfgCardViewProfileLink: { color: neon_magenta, fontWeight: 600, fontSize: '14px', textDecoration: 'none', transition: 'text-shadow 0.2s, letter-spacing 0.2s' },
    mfgCardViewProfileLinkHover: { textShadow: `0 0 5px ${neon_magenta}`, letterSpacing: '0.5px' },
    profilePageContainer: { flexGrow: 1, paddingBottom: '64px' },
    backButton: { display: 'inline-flex', alignItems: 'center', background: 'none', border: `1px solid ${border_color}`, cursor: 'pointer', color: text_primary, fontWeight: 500, fontSize: '15px', padding: '8px 12px', marginBottom: '24px', borderRadius: '8px', backgroundColor: 'rgba(0,0,0,0.3)', transition: 'all 0.2s ease' },
    profileHeader: { position: 'relative', padding: '48px 0', color: '#fff', backgroundSize: 'cover', backgroundPosition: 'center' },
    profileHeaderContent: { display: 'flex', alignItems: 'center', gap: '32px', position: 'relative', zIndex: 2 },
    profileHeaderLogo: { width: '120px', height: '120px', backgroundColor: bg_deep_space, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '4px solid #fff', boxShadow: `0 0 15px #fff`, objectFit: 'cover' },
    profileTitle: { fontSize: '48px', fontWeight: 800, color: '#FFFFFF', margin: 0, textShadow: '0 2px 8px rgba(0,0,0,0.8)' },
    profileLocation: { fontSize: '18px', color: '#E0E7FF', margin: '8px 0 0 0', display: 'flex', alignItems: 'center', textShadow: '0 1px 4px rgba(0,0,0,0.7)' },
    profileContentGrid: { display: 'grid', gridTemplateColumns: 'minmax(0, 2fr) minmax(0, 1fr)', gap: '48px', marginTop: '48px' },
    profileMainContent: { display: 'flex', flexDirection: 'column', gap: '48px' },
    profileSidebar: { display: 'flex', flexDirection: 'column', gap: '32px' },
    profileSection: { backgroundColor: 'rgba(16, 24, 48, 0.4)', borderRadius: '12px', padding: '24px', border: `1px solid ${border_color}` },
    profileSectionTitle: { fontSize: '20px', fontWeight: 600, color: neon_magenta, margin: '0 0 16px 0', paddingBottom: '12px', borderBottom: `1px solid ${border_color}`, textShadow: `0 0 5px ${neon_magenta}` },
    profilePortfolioGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '16px' },
    portfolioItem: { position: 'relative', borderRadius: '8px', overflow: 'hidden', aspectRatio: '4/3', backgroundColor: bg_deep_space, cursor: 'pointer', border: `1px solid ${border_color}` },
    profilePortfolioImage: { width: '100%', height: '100%', objectFit: 'cover', transition: 'transform 0.3s ease' },
    portfolioItemOverlay: { position: 'absolute', bottom: 0, left: 0, right: 0, background: 'linear-gradient(to top, rgba(0,0,0,0.8), transparent)', padding: '16px 12px 8px 12px', transition: 'opacity 0.3s ease' },
    portfolioItemTitle: { color: '#fff', fontWeight: 600, fontSize: '14px', margin: 0, lineHeight: 1.2 },
    portfolioVideoPlaceholder: { width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#374151' },
    dashboardContainer: { display: 'flex', flexGrow: 1, backgroundColor: 'rgba(2, 4, 10, 0.5)' },
    dashboardSidebar: { width: '280px', backgroundColor: 'rgba(2, 4, 10, 0.7)', backdropFilter: 'blur(10px)', color: text_primary, padding: '24px', display: 'flex', flexDirection: 'column', borderRight: `1px solid ${border_color}` },
    dashboardSidebarTitle: { fontSize: '20px', fontWeight: 600, color: '#FFFFFF', lineHeight: 1.3, margin: '0 0 32px 0', textShadow: `0 0 5px ${neon_cyan}` },
    dashboardNav: { display: 'flex', flexDirection: 'column', gap: '8px' },
    dashboardNavLink: { display: 'flex', alignItems: 'center', padding: '12px 16px', borderRadius: '8px', textDecoration: 'none', color: text_secondary, fontWeight: 500, transition: 'all 0.2s', border: '1px solid transparent' },
    dashboardNavLinkActive: { backgroundColor: 'rgba(10, 240, 240, 0.1)', color: neon_cyan, border: `1px solid ${neon_cyan}` },
    dashboardMainContent: { flex: 1, padding: '48px', overflowY: 'auto' },
    dashboardPageTitle: { fontSize: '32px', fontWeight: 700, color: text_primary, margin: '0 0 8px 0', textShadow: `0 0 8px ${neon_cyan}` },
    dashboardPageSubtitle: { fontSize: '16px', color: text_secondary, margin: '0 0 32px 0' },
    statsGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '24px', marginTop: '32px' },
    statCard: { backgroundColor: 'rgba(16, 24, 48, 0.6)', padding: '24px', borderRadius: '12px', border: `1px solid ${border_color}`, boxShadow: 'inset 0 0 10px rgba(240, 5, 180, 0.1)' },
    statValue: { fontSize: '36px', fontWeight: 700, color: neon_cyan, margin: '0 0 4px 0', textShadow: `0 0 8px ${neon_cyan}` },
    statLabel: { fontSize: '14px', color: text_secondary, margin: 0, fontWeight: 500 },
    tableContainer: { backgroundColor: 'rgba(16, 24, 48, 0.4)', borderRadius: '12px', border: `1px solid ${border_color}`, overflow: 'hidden' },
    table: { width: '100%', borderCollapse: 'collapse' },
    tableHeader: { backgroundColor: 'rgba(2, 4, 10, 0.7)', padding: '12px 16px', textAlign: 'left', fontSize: '12px', fontWeight: 600, color: text_secondary, textTransform: 'uppercase', letterSpacing: '0.05em', borderBottom: `1px solid ${border_color_strong}` },
    tableCell: { padding: '16px', borderTop: `1px solid ${border_color}`, fontSize: '14px', color: text_secondary, verticalAlign: 'middle' },
    statusBadge: { padding: '4px 10px', borderRadius: '9999px', fontSize: '12px', fontWeight: 600, display: 'inline-block', whiteSpace: 'nowrap', border: '1px solid' },
    modalBackdrop: { position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(2, 4, 10, 0.7)', backdropFilter: 'blur(8px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: '16px' },
    modalContent: { backgroundColor: 'rgba(2, 4, 10, 0.9)', padding: '24px', borderRadius: '12px', width: '100%', maxWidth: '600px', boxShadow: `0 0 40px rgba(10, 240, 240, 0.4)`, overflowY: 'auto', maxHeight: '90vh', border: `1px solid ${neon_cyan}` },
    modalHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: `1px solid ${border_color}`, paddingBottom: '16px', marginBottom: '16px' },
    modalTitle: { fontSize: '20px', fontWeight: 600, color: text_primary, margin: 0, textShadow: `0 0 5px ${neon_cyan}` },
    modalCloseButton: { background: 'none', border: 'none', cursor: 'pointer', color: text_secondary },
    modalBody: {},
    modalFooter: { display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '24px', borderTop: `1px solid ${border_color}`, paddingTop: '16px' },
    quoteDetailsGrid: { display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px 24px' },
    quoteDetailLabel: { fontSize: '12px', color: text_secondary, margin: '0 0 4px 0', textTransform: 'uppercase' },
    quoteDetailValue: { fontSize: '16px', color: text_primary, margin: 0, fontWeight: 500 },
    fileListItem: { display: 'flex', alignItems: 'center', gap: '16px', padding: '12px', backgroundColor: 'rgba(0,0,0,0.3)', borderRadius: '8px' },
    fileInfo: { flexGrow: 1 },
    fileName: { fontWeight: 500, color: text_primary },
    fileSize: { fontSize: '12px', color: text_secondary },
    imageUploadBox: { position: 'relative', width: '100%', aspectRatio: '16 / 9', backgroundColor: 'rgba(16, 24, 48, 0.4)', border: `2px dashed ${border_color_strong}`, borderRadius: '8px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden', transition: 'all 0.3s' },
    imageUploadPreview: { width: '100%', height: '100%', objectFit: 'cover' },
    imageUploadPlaceholder: { display: 'flex', flexDirection: 'column', alignItems: 'center' },
    imageUploadRemoveBtn: { position: 'absolute', top: '8px', right: '8px', background: 'rgba(0,0,0,0.7)', color: 'white', border: 'none', cursor: 'pointer', borderRadius: '50%', width: '28px', height: '28px', display: 'flex', alignItems: 'center', justifyContent: 'center', transition: 'background-color 0.2s' },
    portfolioManagementGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: '16px', marginTop: '16px' },
    portfolioManagementItem: { position: 'relative', display: 'flex', flexDirection: 'column', gap: '8px' },
    portfolioManagementImage: { width: '100%', aspectRatio: '1 / 1', objectFit: 'cover', borderRadius: '8px', border: `1px solid ${border_color}` },
    portfolioManagementTitleInput: { width: '100%', padding: '8px', border: `1px solid ${border_color_strong}`, borderRadius: '6px', fontSize: '12px', backgroundColor: 'rgba(0,0,0,0.3)', color: text_primary },
};

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);