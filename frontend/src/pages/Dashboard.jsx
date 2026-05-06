
import { useState, useEffect } from "react"
import { useAuth } from "../context/AuthContext"
import { useNavigate } from "react-router-dom"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../components/ui/card"
import { Button } from "../components/ui/button"
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from "../components/ui/table"
import { Badge } from "../components/ui/badge"
import { Input } from "../components/ui/input"
import { Search, Database, HardDrive, RefreshCw, LogOut } from "lucide-react"

export default function Dashboard() {
  const { connection, logout, apiCall } = useAuth()
  const navigate = useNavigate()
  const [databases, setDatabases] = useState([])
  const [loading, setLoading] = useState(true)
  const [backuping, setBackuping] = useState(null)
  const [search, setSearch] = useState("")
  const [error, setError] = useState("")

  useEffect(() => {
    if (!connection) {
      navigate("/")
      return
    }
    fetchDatabases()
  }, [connection, navigate])

  const fetchDatabases = async () => {
    setLoading(true)
    setError("")
    try {
      const data = await apiCall("/api/databases")
      setDatabases(data)
    } catch (err) {
      setError(err.message)
      if (err.message.includes("Login failed")) {
          logout()
      }
    } finally {
      setLoading(false)
    }
  }

  const handleBackup = async (dbName) => {
    setBackuping(dbName)
    try {
      await apiCall("/api/backup", "POST", { db_name: dbName })
      // Show success toast or notification (omitted for brevity)
      alert(`Backup of ${dbName} started/completed successfully!`)
    } catch (err) {
      alert(`Backup failed: ${err.message}`)
    } finally {
      setBackuping(null)
    }
  }

  const navigateToDetails = (dbName) => {
      navigate(`/database/${dbName}`)
  }

  const filteredDatabases = databases.filter(db => 
    db.name.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-zinc-950">
      <header className="bg-white dark:bg-zinc-900 border-b p-4 flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center space-x-2">
          <Database className="h-6 w-6 text-primary" />
          <h1 className="text-xl font-bold">MSSQL Manager</h1>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-sm text-muted-foreground hidden md:block">
            Connected to: <span className="font-medium text-foreground">{connection?.host}</span> ({connection?.user})
          </div>
          <Button variant="outline" size="sm" onClick={logout}>
            <LogOut className="h-4 w-4 mr-2" />
            Disconnect
          </Button>
        </div>
      </header>

      <main className="container mx-auto p-6 space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-3xl font-bold tracking-tight">Databases</h2>
          <Button onClick={fetchDatabases} disabled={loading} variant="outline">
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {error && (
            <div className="p-4 text-red-500 bg-red-50 border border-red-200 rounded-md">
                Error: {error}
            </div>
        )}

        <div className="flex items-center space-x-2 mb-4">
            <Search className="h-4 w-4 text-muted-foreground" />
            <Input 
                placeholder="Search databases..." 
                className="max-w-sm"
                value={search}
                onChange={(e) => setSearch(e.target.value)} 
            />
        </div>

        <Card>
            <CardContent className="p-0">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Name</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>Recovery Model</TableHead>
                            <TableHead className="text-right">Size (MB)</TableHead>
                            <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {loading ? (
                             <TableRow>
                                <TableCell colSpan={5} className="text-center h-24">Loading...</TableCell>
                            </TableRow>
                        ) : filteredDatabases.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={5} className="text-center h-24">No databases found</TableCell>
                            </TableRow>
                        ) : (
                            filteredDatabases.map((db) => (
                                <TableRow key={db.id} className="cursor-pointer hover:bg-muted/50" onClick={() => navigateToDetails(db.name)}>
                                    <TableCell className="font-medium">
                                        <div className="flex items-center space-x-2">
                                            <Database className="h-4 w-4 text-muted-foreground" />
                                            <span>{db.name}</span>
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        <Badge variant={db.state === 'ONLINE' ? 'default' : 'destructive'}>
                                            {db.state}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>{db.recovery_model}</TableCell>
                                    <TableCell className="text-right">{db.size_mb.toFixed(2)}</TableCell>
                                    <TableCell className="text-right" onClick={(e) => e.stopPropagation()}>
                                        <div className="flex justify-end space-x-2">
                                            <Button 
                                                variant="secondary" 
                                                size="sm"
                                                onClick={() => handleBackup(db.name)}
                                                disabled={backuping === db.name}
                                            >
                                                {backuping === db.name ? (
                                                    <RefreshCw className="h-3 w-3 animate-spin mr-1" />
                                                ) : (
                                                    <HardDrive className="h-3 w-3 mr-1" />
                                                )}
                                                Backup
                                            </Button>
                                        </div>
                                    </TableCell>
                                </TableRow>
                            ))
                        )}
                    </TableBody>
                </Table>
            </CardContent>
        </Card>
      </main>
    </div>
  )
}
