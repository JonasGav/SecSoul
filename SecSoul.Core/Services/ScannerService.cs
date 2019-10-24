using Microsoft.Extensions.Options;
using SecSoul.Core.Options;
using System;
using System.Collections.Generic;
using System.Text;

namespace SecSoul.Core.Services
{
    public class ScannerService
    {
        private PythonService _python;
        private PythonOptions _pythonOptions;
        public ScannerService(PythonService python, IOptionsMonitor<PythonOptions> pythonOptions)
        {
            _python = python;
            _pythonOptions = pythonOptions.CurrentValue;
        }
        public void StartScanning(string url)
        {
            _python.run_cmd(_pythonOptions.PythonExeLoc, _pythonOptions.PythonToolScript, url);
        }
    }
}
