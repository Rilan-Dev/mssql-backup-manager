
import { useState, useEffect } from "react"
import { useAuth } from "../context/AuthContext"
import { useParams, useNavigate } from "react-router-dom"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../components/ui/card"
import { Button } from "../components/ui/button"
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from "../components/ui/table"
import { Badge } from "../components/ui/badge"
import { ArrowLeft, HardDrive, RefreshCw, RotateCcw } from "lucide-react"

export default function DatabaseDetails() {
  const { connection, apiCall } = useAuth()
  const { dbName } = useParams()
  const navigate = useNavigate()
  
  const [dbInfo, setDbInfo] = useState(null)
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState("")

  useEffect(() => {
    if (!connection) {
      navigate("/")
      return
    }
    fetchData()
  }, [connection, dbName, navigate])

  const fetchData = async () => {
    setLoading(true)
    setError("")
    try {
      const info = await apiCall(`/api/databases/${dbName}`)
      setDbInfo(info)
      
      const historyData = await apiCall(`/api/databases/${dbName}/history`, 'POST')
      setHistory(historyData)
      
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleBackup = async () => {
    setActionLoading(true)
    try {
      await apiCall("/api/backup", "POST", { db_name: dbName })
      alert(`Backup of ${dbName} completed successfully!`)
      fetchData() // Refresh logic
    } catch (err) {
      alert(`Backup failed: ${err.message}`)
    } finally {
      setActionLoading(false)
    }
  }

  const handleRestore = async (backupFile) => {
      if (!window.confirm(`Are you sure you want to restore ${dbName} from ${backupFile}? This will overwrite current data!`)) {
          return
      }
      
      setActionLoading(true)
      try {
        await apiCall("/api/restore", "POST", { 
            db_name: dbName, 
            backup_file: backupFile, 
            force: true 
        })
        alert(`Restore of ${dbName} completed successfully!`)
        fetchData()
      } catch (err) {
        alert(`Restore failed: ${err.message}`)
      } finally {
        setActionLoading(false)
      }
  }

  if (loading) return <div className="p-8 text-center">Loading details...</div>
  if (error) return <div className="p-8 text-center text-red-500">Error: {error}</div>
  if (!dbInfo) return <div className="p-8 text-center">Database not found</div>

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-zinc-950 p-6">
      <div className="container mx-auto space-y-6">
        <Button variant="ghost" onClick={() => navigate("/dashboard")} className="mb-4">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Dashboard
        </Button>

        <div className="grid gap-6 md:grid-cols-2">
            <Card>
                <CardHeader>
                    <CardTitle className="text-2xl">{dbInfo.name}</CardTitle>
                    <CardDescription>Database Information</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <div className="text-sm font-medium text-muted-foreground">Status</div>
                            <Badge variant={dbInfo.state_desc === 'ONLINE' ? 'default' : 'destructive'}>
                                {dbInfo.state_desc}
                            </Badge>
                        </div>
                        <div>
                             <div className="text-sm font-medium text-muted-foreground">Recovery Model</div>
                             <div>{dbInfo.recovery_model_desc}</div>
                        </div>
                        <div>
                             <div className="text-sm font-medium text-muted-foreground">Data Size</div>
                             <div>{dbInfo.data_size_mb ? dbInfo.data_size_mb.toFixed(2) : 0} MB</div>
                        </div>
                        <div>
                             <div className="text-sm font-medium text-muted-foreground">Log Size</div>
                             <div>{dbInfo.log_size_mb ? dbInfo.log_size_mb.toFixed(2) : 0} MB</div>
                        </div>
                        <div>
                             <div className="text-sm font-medium text-muted-foreground">Created</div>
                             <div>{new Date(dbInfo.create_date).toLocaleDateString()}</div>
                        </div>
                    </div>
                    
                    <div className="pt-4 flex space-x-4">
                        <Button onClick={handleBackup} disabled={actionLoading}>
                            {actionLoading ? <RefreshCw className="h-4 w-4 mr-2 animate-spin"/> : <HardDrive className="h-4 w-4 mr-2"/>}
                            Backup Now
                        </Button>
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardHeader>
                    <CardTitle>Backup History</CardTitle>
                    <CardDescription>Recent backups for this database</CardDescription>
                </CardHeader>
                <CardContent>
                    {history.length === 0 ? (
                        <div className="text-center text-muted-foreground py-8">
                            No backup history found.
                        </div>
                    ) : (
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Date</TableHead>
                                    <TableHead>Type</TableHead>
                                    <TableHead>Size (MB)</TableHead>
                                    <TableHead>File</TableHead>
                                    <TableHead className="text-right">Action</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {history.map((backup, idx) => (
                                    <TableRow key={idx}>
                                        <TableCell>{new Date(backup.start_time).toLocaleString()}</TableCell>
                                        <TableCell>{backup.type}</TableCell>
                                        <TableCell>{backup.size_mb.toFixed(2)}</TableCell>
                                        <TableCell className="max-w-[200px] truncate" title={backup.file}>{backup.file.split(/[/\\]/).pop()}</TableCell>
                                        <TableCell className="text-right">
                                            <Button 
                                                variant="outline" 
                                                size="sm"
                                                onClick={() => handleRestore(backup.file)}
                                                disabled={actionLoading}
                                            >
                                                <RotateCcw className="h-3 w-3 mr-1" />
                                                Restore
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    )}
                </CardContent>
            </Card>
        </div>
      </div>
    </div>
  )
}
