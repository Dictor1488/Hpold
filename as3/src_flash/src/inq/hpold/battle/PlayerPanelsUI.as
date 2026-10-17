package inq.hpold.battle
{
   import flash.display.DisplayObjectContainer;
   import flash.text.TextField;
   import flash.text.TextFormat;
   import flash.utils.Dictionary;
   import inq.hpold.injector.BattleDisplayable;

   /**
    * Source reconstruction from the AVM2 bytecode in
    * playersPanelAPI_modsCore.swf (OldSkool).
    *
    * The original draws no shapes, does not scale labels and does not
    * reflow the fields each frame. Every field is attached directly to
    * the corresponding player panel list item, above vehicleTF.
    */
   public class PlayerPanelsUI extends BattleDisplayable
   {
      private var configs:Object = {};
      private var textFields:Object = {};

      public function PlayerPanelsUI()
      {
         super();
      }

      public function as_create(linkage:String, kind:String, config:Object):void
      {
         if (linkage == null || config == null || kind != "Label")
            return;
         configs[linkage] = config;
         if (!textFields.hasOwnProperty(linkage))
            textFields[linkage] = {};
      }

      public function as_update(linkage:String, data:Object):void
      {
         if (!textFields.hasOwnProperty(linkage) || data == null ||
             !data.hasOwnProperty("vehicleID"))
            return;

         var entries:Object = textFields[linkage];
         var vehicleID:String = String(data.vehicleID);
         if (!entries.hasOwnProperty(vehicleID))
            _createTextField(linkage, data);
         if (!entries.hasOwnProperty(vehicleID))
            return;

         var field:TextField = entries[vehicleID] as TextField;
         if (configs[linkage].isHtml)
            field.htmlText = String(data.text);
         else
            field.text = String(data.text);
      }

      public function as_delete(linkage:String):void
      {
         if (!textFields.hasOwnProperty(linkage))
            return;
         var entries:Object = textFields[linkage];
         for (var vehicleID:String in entries)
         {
            var field:TextField = entries[vehicleID] as TextField;
            if (field != null && field.parent != null)
               field.parent.removeChild(field);
         }
         delete textFields[linkage];
         delete configs[linkage];
      }

      private function _createTextField(linkage:String, data:Object):void
      {
         try
         {
            if (battlePage == null || !battlePage.hasOwnProperty("playersPanel") ||
                !configs.hasOwnProperty(linkage))
               return;

            var panel:* = battlePage["playersPanel"];
            var holder:* = panel.listLeft.getHolderByVehicleID(data["vehicleID"]);
            var side:String = "left";
            if (holder == null)
            {
               side = "right";
               holder = panel.listRight.getHolderByVehicleID(data["vehicleID"]);
            }
            if (holder == null || !configs[linkage].hasOwnProperty(side))
               return;

            var cfg:Object = configs[linkage][side];
            var item:DisplayObjectContainer = holder._listItem as DisplayObjectContainer;
            if (item == null || holder._listItem.vehicleIcon == null ||
                holder._listItem.vehicleTF == null)
               return;

            var field:TextField = new TextField();
            field.visible = true;
            // OldSkool configs omit dimensions on HP text labels.
            // Number(undefined) makes the Flash TextField size NaN and hides text.
            field.height = cfg.hasOwnProperty("height") ? Number(cfg.height) : 24;
            field.width = cfg.hasOwnProperty("width") ? Number(cfg.width) : 100;
            field.selectable = false;
            field.mouseEnabled = false;
            field.wordWrap = false;
            field.multiline = false;
            field.embedFonts = false;
            var format:TextFormat = new TextFormat("$FieldFont", 11, 0xFFFFFF);
            format.align = cfg.hasOwnProperty("align") ? String(cfg.align) : side;
            field.defaultTextFormat = format;
            field.x = Number(holder._listItem.vehicleIcon.x) +
                      (cfg.hasOwnProperty("x") ? Number(cfg.x) : 0);
            field.y = Number(holder._listItem.vehicleIcon.y) +
                      (cfg.hasOwnProperty("y") ? Number(cfg.y) : 0);

            // Exact placement in the original ABC: one layer after vehicleTF.
            item.addChildAt(field, item.getChildIndex(holder._listItem.vehicleTF) + 1);
            textFields[linkage][String(data["vehicleID"])] = field;
         }
         catch (error:Error)
         {
            trace("[inq_hpold] PlayerPanelsUI._createTextField: " + error.message);
         }
      }

      override protected function onDispose():void
      {
         for (var linkage:String in textFields)
            as_delete(linkage);
         super.onDispose();
      }
   }
}
