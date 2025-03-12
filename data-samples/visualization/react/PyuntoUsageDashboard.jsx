import React, { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { Card, CardHeader, CardContent, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Button } from './ui/button';
import { Calendar } from './ui/calendar';
import { format } from 'date-fns';

// Sample colors
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82ca9d'];

/**
 * Pyunto Intelligence Usage Dashboard Component
 * 
 * This component visualizes API usage data from Pyunto Intelligence.
 */
const PyuntoUsageDashboard = ({ apiKey, assistantId }) => {
  const [usageData, setUsageData] = useState(null);
  const [dateRange, setDateRange] = useState('month'); // 'day', 'week', 'month', 'year'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [startDate, setStartDate] = useState(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)); // 30 days ago
  const [endDate, setEndDate] = useState(new Date());
  const [filteredData, setFilteredData] = useState([]);
  const [assistants, setAssistants] = useState([]);
  const [selectedAssistant, setSelectedAssistant] = useState(assistantId || 'all');

  // Fetch data on component mount or when dependencies change
  useEffect(() => {
    if (apiKey) {
      fetchUsageData();
      fetchAssistants();
    }
  }, [apiKey, dateRange]);

  // Filter data when date range or assistant selection changes
  useEffect(() => {
    if (usageData) {
      filterDataByDateAndAssistant();
    }
  }, [usageData, startDate, endDate, selectedAssistant]);

  const fetchUsageData = async () => {
    setLoading(true);
    setError(null);

    try {
      // In a real application, this would be an API call to Pyunto Intelligence
      // const response = await fetch('https://a.pyunto.com/api/usage', {
      //   headers: {
      //     'Authorization': `Bearer ${apiKey}`,
      //     'Content-Type': 'application/json'
      //   }
      // });
      // const data = await response.json();

      // For demo purposes, we'll use sample data
      const data = generateSampleData();
      setUsageData(data);
      setFilteredData(data);
    } catch (err) {
      console.error('Error fetching usage data:', err);
      setError('Failed to fetch usage data. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const fetchAssistants = async () => {
    try {
      // In a real application, this would be an API call to Pyunto Intelligence
      // const response = await fetch('https://a.pyunto.com/api/assistants', {
      //   headers: {
      //     'Authorization': `Bearer ${apiKey}`,
      //     'Content-Type': 'application/json'
      //   }
      // });
      // const data = await response.json();

      // For demo purposes, we'll use sample data
      setAssistants([
        { id: 'assistant-1', name: 'Product Analyzer' },
        { id: 'assistant-2', name: 'Menu Item Recognizer' },
        { id: 'assistant-3', name: 'Text Extractor' },
      ]);
    } catch (err) {
      console.error('Error fetching assistants:', err);
    }
  };

  const filterDataByDateAndAssistant = () => {
    if (!usageData) return;

    const filtered = usageData.filter(item => {
      const itemDate = new Date(item.date);
      const dateInRange = itemDate >= startDate && itemDate <= endDate;
      const assistantMatch = selectedAssistant === 'all' || item.assistantId === selectedAssistant;
      return dateInRange && assistantMatch;
    });

    setFilteredData(filtered);
  };

  const generateSampleData = () => {
    // Generate sample usage data for the past 90 days
    const data = [];
    const now = new Date();

    for (let i = 90; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(now.getDate() - i);
      
      // Generate random data for each assistant
      const assistantIds = ['assistant-1', 'assistant-2', 'assistant-3'];
      
      assistantIds.forEach(assistantId => {
        // Base value that increases over time to simulate growing usage
        const baseValue = Math.max(5, 90 - i);
        
        // Random daily fluctuation
        const randomFactor = 0.5 + Math.random();
        
        // Weekend effect (less usage on weekends)
        const dayOfWeek = date.getDay();
        const weekendFactor = (dayOfWeek === 0 || dayOfWeek === 6) ? 0.7 : 1;
        
        // Calculate final call count
        const calls = Math.floor(baseValue * randomFactor * weekendFactor);
        
        // Add entry
        data.push({
          date: date.toISOString().split('T')[0],
          calls,
          errors: Math.floor(calls * 0.03 * Math.random()),
          latency: 100 + Math.floor(Math.random() * 400),
          assistantId,
          type: ['image', 'text', 'audio'][Math.floor(Math.random() * 3)],
        });
      });
    }

    return data;
  };

  const handleDateRangeChange = (range) => {
    setDateRange(range);
    const now = new Date();

    switch (range) {
      case 'day':
        setStartDate(new Date(now.setDate(now.getDate() - 1)));
        break;
      case 'week':
        setStartDate(new Date(now.setDate(now.getDate() - 7)));
        break;
      case 'month':
        setStartDate(new Date(now.setDate(now.getDate() - 30)));
        break;
      case 'year':
        setStartDate(new Date(now.setFullYear(now.getFullYear() - 1)));
        break;
      default:
        setStartDate(new Date(now.setDate(now.getDate() - 30)));
    }
    setEndDate(new Date());
  };

  const aggregateDataByDate = () => {
    if (!filteredData.length) return [];
    
    // Group data by date
    const groupedByDate = filteredData.reduce((acc, item) => {
      if (!acc[item.date]) {
        acc[item.date] = { date: item.date, calls: 0, errors: 0 };
      }
      acc[item.date].calls += item.calls;
      acc[item.date].errors += item.errors;
      return acc;
    }, {});
    
    // Convert to array and sort by date
    return Object.values(groupedByDate).sort((a, b) => 
      new Date(a.date) - new Date(b.date)
    );
  };

  const aggregateDataByType = () => {
    if (!filteredData.length) return [];
    
    // Group data by type
    const groupedByType = filteredData.reduce((acc, item) => {
      if (!acc[item.type]) {
        acc[item.type] = { type: item.type, calls: 0 };
      }
      acc[item.type].calls += item.calls;
      return acc;
    }, {});
    
    // Convert to array
    return Object.values(groupedByType);
  };

  const aggregateDataByAssistant = () => {
    if (!filteredData.length) return [];
    
    // Group data by assistant
    const groupedByAssistant = filteredData.reduce((acc, item) => {
      if (!acc[item.assistantId]) {
        const assistantName = assistants.find(a => a.id === item.assistantId)?.name || item.assistantId;
        acc[item.assistantId] = { 
          assistantId: item.assistantId,
          name: assistantName,
          calls: 0 
        };
      }
      acc[item.assistantId].calls += item.calls;
      return acc;
    }, {});
    
    // Convert to array
    return Object.values(groupedByAssistant);
  };

  const calculateTotalUsage = () => {
    if (!filteredData.length) return { calls: 0, errors: 0, successRate: 0 };
    
    const totalCalls = filteredData.reduce((sum, item) => sum + item.calls, 0);
    const totalErrors = filteredData.reduce((sum, item) => sum + item.errors, 0);
    const successRate = totalCalls > 0 ? ((totalCalls - totalErrors) / totalCalls * 100).toFixed(2) : 0;
    
    return { calls: totalCalls, errors: totalErrors, successRate };
  };

  // If still loading or no API key, show loading or configuration required
  if (!apiKey) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Pyunto Intelligence Usage Dashboard</CardTitle>
        </CardHeader>
        <CardContent>
          <p>Please configure your API key to view usage metrics.</p>
        </CardContent>
      </Card>
    );
  }

  if (loading && !usageData) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Pyunto Intelligence Usage Dashboard</CardTitle>
        </CardHeader>
        <CardContent>
          <p>Loading usage data...</p>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Pyunto Intelligence Usage Dashboard</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-red-500">{error}</p>
          <Button onClick={fetchUsageData}>Retry</Button>
        </CardContent>
      </Card>
    );
  }

  const dateAggregatedData = aggregateDataByDate();
  const typeAggregatedData = aggregateDataByType();
  const assistantAggregatedData = aggregateDataByAssistant();
  const { calls: totalCalls, errors: totalErrors, successRate } = calculateTotalUsage();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Pyunto Intelligence Usage Dashboard</h2>
        <div className="flex items-center space-x-2">
          <Select value={dateRange} onValueChange={handleDateRangeChange}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Date Range" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="day">Last Day</SelectItem>
              <SelectItem value="week">Last Week</SelectItem>
              <SelectItem value="month">Last Month</SelectItem>
              <SelectItem value="year">Last Year</SelectItem>
            </SelectContent>
          </Select>
          
          <Select value={selectedAssistant} onValueChange={setSelectedAssistant}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Select Assistant" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Assistants</SelectItem>
              {assistants.map(assistant => (
                <SelectItem key={assistant.id} value={assistant.id}>
                  {assistant.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          <Button variant="outline" onClick={fetchUsageData}>
            Refresh
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total API Calls</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalCalls.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              {format(startDate, 'MMM d, yyyy')} - {format(endDate, 'MMM d, yyyy')}
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{successRate}%</div>
            <p className="text-xs text-muted-foreground">
              {totalErrors.toLocaleString()} errors out of {totalCalls.toLocaleString()} calls
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Active Assistants</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{assistantAggregatedData.length}</div>
            <p className="text-xs text-muted-foreground">
              Assistants with usage in the selected period
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="usage">
        <TabsList>
          <TabsTrigger value="usage">Usage Over Time</TabsTrigger>
          <TabsTrigger value="assistants">Usage by Assistant</TabsTrigger>
          <TabsTrigger value="types">Usage by Type</TabsTrigger>
        </TabsList>
        
        <TabsContent value="usage" className="pt-4">
          <Card>
            <CardHeader>
              <CardTitle>API Calls Over Time</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={dateAggregatedData}
                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="calls"
                      stroke="#8884d8"
                      name="API Calls"
                      activeDot={{ r: 8 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="errors"
                      stroke="#ff0000"
                      name="Errors"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="assistants" className="pt-4">
          <Card>
            <CardHeader>
              <CardTitle>Usage by Assistant</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={assistantAggregatedData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="calls"
                        nameKey="name"
                      >
                        {assistantAggregatedData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={assistantAggregatedData}
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="calls" name="API Calls">
                        {assistantAggregatedData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="types" className="pt-4">
          <Card>
            <CardHeader>
              <CardTitle>Usage by Data Type</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={typeAggregatedData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ type, percent }) => `${type}: ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="calls"
                        nameKey="type"
                      >
                        {typeAggregatedData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={typeAggregatedData}
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="type" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="calls" name="API Calls">
                        {typeAggregatedData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default PyuntoUsageDashboard;
