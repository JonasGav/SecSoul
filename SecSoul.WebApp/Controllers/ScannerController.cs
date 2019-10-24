using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using SecSoul.Core.Services;

// For more information on enabling MVC for empty projects, visit https://go.microsoft.com/fwlink/?LinkID=397860

namespace SecSoul.WebApp.Controllers
{
    public class ScannerController : Controller
    {

        private ScannerService _scannerService;
        public ScannerController(ScannerService scannerService)
        {
            _scannerService = scannerService;
        }
        // GET: /<controller>/
        public IActionResult Index()
        {
            return View();
        }
        [HttpGet("Scan/StartScanning")]
        public void StartScan(string url)
        {
            _scannerService.StartScanning(url);
        }
    }
}
